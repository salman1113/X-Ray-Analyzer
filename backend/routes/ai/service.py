"""
AI Analysis orchestrator — multi-body-part pipeline.

Ties together:
  1. body_parts    → look up conditions and config for the requested body part
  2. preprocessing → load & normalize the X-ray image
  3. inference     → run body-part-specific DenseNet121
  4. gradcam       → generate heatmap overlay image
  5. scan DB       → save result, update status
"""

import logging

from motor.motor_asyncio import AsyncIOMotorDatabase

from core.exceptions import BadRequestException
from routes.ai.body_parts import get_body_part
from routes.ai.gradcam import generate_gradcam
from routes.ai.inference import get_model, run_inference
from routes.ai.patient_language import get_patient_summary
from routes.ai.preprocessing import preprocess_image
from routes.scan.service import get_scan, save_ai_result

logger = logging.getLogger(__name__)

GRADCAM_OUTPUT_DIR = "uploads/gradcam"


async def analyze_scan(
    scan_id: str,
    tenant_db: AsyncIOMotorDatabase,
    body_part: str = "chest",
) -> dict:
    """
    Full AI analysis pipeline for a single X-ray scan.

    Args:
        scan_id:    Unique scan identifier.
        tenant_db:  Tenant-specific MongoDB database.
        body_part:  Which body part to analyze.
                    e.g. "chest", "knee", "hand", "spine", "hip" …
                    Defaults to "chest" for backwards compatibility.

    Steps:
        1. Validate body_part exists in registry.
        2. Fetch scan + validate image is uploaded.
        3. Mark status → 'processing'.
        4. Preprocess image → tensor.
        5. Run body-part-specific DenseNet121 → prediction + confidence.
        6. Generate Grad-CAM heatmap.
        7. Persist ai_result → status 'analyzed'.

    Returns:
        Updated scan document with ai_result populated.
    """
    # ── 1. Validate body part ───────────────────────────────────────────────
    try:
        cfg = get_body_part(body_part)
    except KeyError as e:
        raise BadRequestException(str(e)) from e

    # ── 2. Load scan & validate ─────────────────────────────────────────────
    scan = await get_scan(scan_id, tenant_db)

    if not scan.get("image_path"):
        raise BadRequestException("Scan has no uploaded image. Upload the X-ray image first.")

    # Idempotent — return cached result if already analyzed for same body part
    if (
        scan.get("status") == "analyzed"
        and scan.get("ai_result")
        and scan["ai_result"].get("body_part") == body_part
    ):
        logger.info("Scan %s already analyzed (%s) — returning cached result.", scan_id, body_part)
        return scan

    # ── 3. Mark as processing ───────────────────────────────────────────────
    await tenant_db.scans.update_one(
        {"scan_id": scan_id},
        {
            "$set": {
                "status": "processing",
                "body_part": body_part,
            }
        },
    )
    logger.info("Starting AI analysis: scan=%s  body_part=%s", scan_id, body_part)

    try:
        image_path = scan["image_path"]

        # ── 4. Preprocess ───────────────────────────────────────────────────
        tensor, _pil = await preprocess_image(image_path)

        # ── 5. Inference (body-part-specific) ──────────────────────────────
        inference_result = await run_inference(tensor, body_part_key=body_part)
        prediction = inference_result["prediction"]
        confidence = inference_result["confidence"]
        probabilities = inference_result["probabilities"]

        # Map prediction → class index for Grad-CAM
        class_idx = cfg.conditions.index(prediction) if prediction in cfg.conditions else 0

        logger.info(
            "Scan %s [%s] → %s  %.1f%%",
            scan_id,
            body_part,
            prediction,
            confidence * 100,
        )

        # ── 6. Grad-CAM heatmap ─────────────────────────────────────────────
        model = get_model(body_part)
        gradcam_path = await generate_gradcam(
            image_path=image_path,
            model=model,
            tensor=tensor,
            predicted_class_idx=class_idx,
            output_dir=GRADCAM_OUTPUT_DIR,
            scan_id=scan_id,
        )

        local_explanation = _build_explanation(body_part, cfg, prediction, confidence)
        local_summary = get_patient_summary(body_part, prediction, confidence)

        from services.llm import generate_llm_explanations

        patient_summary, rag_explanation = await generate_llm_explanations(
            body_part=body_part,
            body_part_label=cfg.label,
            prediction=prediction,
            confidence=confidence,
            probabilities=probabilities,
            local_patient_summary=local_summary,
            local_clinical_explanation=local_explanation,
        )

        # ── 7. Persist results ──────────────────────────────────────────────
        ai_result = {
            "body_part": body_part,
            "body_part_label": cfg.label,
            "prediction": prediction,
            "confidence": confidence,
            "probabilities": probabilities,
            "gradcam_path": gradcam_path,
            "rag_explanation": rag_explanation,
            "patient_summary": patient_summary,
        }

        return await save_ai_result(scan_id, ai_result, tenant_db)

    except FileNotFoundError as e:
        logger.error("Image missing for scan %s: %s", scan_id, e)
        await tenant_db.scans.update_one({"scan_id": scan_id}, {"$set": {"status": "failed"}})
        raise BadRequestException(f"Image file not found: {e}") from e

    except Exception as e:
        logger.exception("AI analysis failed for scan %s [%s]", scan_id, body_part)
        await tenant_db.scans.update_one({"scan_id": scan_id}, {"$set": {"status": "failed"}})
        raise BadRequestException(f"Analysis failed: {e}") from e


def _build_explanation(
    body_part: str,
    cfg,
    prediction: str,
    confidence: float,
) -> str:
    """
    Generate a plain-language clinical explanation based on body part + prediction.
    Replace with a RAG pipeline call for richer, evidence-based notes.
    """
    pct = round(confidence * 100, 1)
    part_label = cfg.label

    if prediction == "Normal":
        return (
            "### Findings Summary\n"
            f"- AI prediction: Normal ({pct}% confidence).\n"
            f"- No significant abnormalities detected in the {part_label} X-ray.\n\n"
            "### Differential Diagnosis & Significance\n"
            "- Findings are within standard physiological limits.\n\n"
            "### Recommendations\n"
            "- Routine clinical follow-up as indicated.\n"
            "- Correlate with patient's baseline history."
        )

    # Body-part-specific clinical context
    clinical_notes = {
        (
            "chest",
            "Pneumonia",
        ): "Radiographic features such as consolidation or infiltrates may be present in the lung fields.",
        (
            "knee",
            "Osteoarthritis",
        ): "Findings may include joint space narrowing, osteophyte formation, or subchondral sclerosis.",
        (
            "knee",
            "Fracture",
        ): "A cortical break or trabecular disruption may be visible in the knee region.",
        (
            "knee",
            "Effusion",
        ): "Increased soft tissue density around the joint may indicate synovial effusion.",
        (
            "hand",
            "Fracture",
        ): "Disruption of the cortical margin may be seen in the metacarpals or phalanges.",
        (
            "hand",
            "Arthritis",
        ): "Joint space narrowing, erosions, or periarticular osteoporosis may be present.",
        (
            "spine",
            "Scoliosis",
        ): "Lateral curvature of the vertebral column is noted. Cobb angle measurement is recommended.",
        (
            "spine",
            "Compression_Fracture",
        ): "Loss of vertebral body height or wedge deformity may indicate a compression fracture.",
        (
            "spine",
            "Disc_Narrowing",
        ): "Reduced intervertebral disc height is observed, which may indicate degenerative disc disease.",
        (
            "hip",
            "Fracture",
        ): "Disruption of the femoral neck or acetabular continuity may be present.",
        (
            "hip",
            "Osteoarthritis",
        ): "Superior joint space narrowing and acetabular osteophytes may be seen.",
        ("shoulder", "Dislocation"): "The humeral head may be displaced from the glenoid fossa.",
        (
            "elbow",
            "Fracture",
        ): "A cortical discontinuity may be seen at the radial head or olecranon.",
        ("foot", "Fracture"): "Metatarsal or phalangeal cortical disruption may be present.",
        (
            "skull",
            "Fracture",
        ): "A linear lucency traversing the calvarium may indicate a skull fracture.",
        (
            "abdomen",
            "Bowel_Obstruction",
        ): "Dilated bowel loops with air-fluid levels are suggestive of obstruction.",
        (
            "abdomen",
            "Free_Air",
        ): "Free intraperitoneal air under the diaphragm may indicate visceral perforation.",
        (
            "leg",
            "Stress_Fracture",
        ): "A periosteal reaction or faint cortical break may suggest a stress fracture.",
    }

    note = clinical_notes.get(
        (body_part, prediction),
        f"The AI model has flagged findings consistent with {prediction.replace('_', ' ')}.",
    )

    return (
        "### Findings Summary\n"
        f"- AI prediction: {prediction.replace('_', ' ')} ({pct}% confidence).\n"
        f"- {note}\n\n"
        "### Differential Diagnosis & Significance\n"
        f"- High-yield indicator of acute/degenerative changes in the {part_label}.\n"
        "- Consider primary presentation details.\n\n"
        "### Recommendations\n"
        "- Immediate clinical correlation with symptoms.\n"
        "- Order confirmatory imaging or lab work if clinically indicated."
    )
