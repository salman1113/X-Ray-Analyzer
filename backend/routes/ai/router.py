from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.dependencies import get_tenant_db, require_doctor
from routes.ai.body_parts import list_body_parts
from routes.ai.schemas import AnalyzeRequest
from routes.ai.service import analyze_scan

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


@router.get("/body-parts")
async def get_body_parts(user: dict = Depends(require_doctor)):
    """
    List all supported X-ray body parts with their detectable conditions.

    Response:
        {
          "chest":   { "label": "Chest / Thorax", "conditions": [...], "description": "..." },
          "knee":    { "label": "Knee",            "conditions": [...], "description": "..." },
          ...
        }
    Frontend can use this to populate the body-part selector dropdown.
    """
    return list_body_parts()


@router.post("/analyze")
async def analyze(
    data: AnalyzeRequest,
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    """
    Trigger AI analysis for a scan.

    Body:
        { "scan_id": "abc-123", "body_part": "knee" }

    Supported body_part values:
        chest, hand, foot, knee, elbow, shoulder, spine,
        hip, forearm, leg, skull, abdomen

    Returns the full scan document with ai_result populated:
        {
          body_part, body_part_label, prediction, confidence,
          probabilities, gradcam_path, rag_explanation
        }
    """
    return await analyze_scan(
        scan_id=data.scan_id,
        tenant_db=tenant_db,
        body_part=data.body_part,
    )


@router.get("/gradcam/{scan_id}")
async def get_gradcam(
    scan_id: str,
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    """
    Serve the Grad-CAM heatmap PNG for a scan.
    Call this after /analyze to get the visual explanation image.

    Returns: image/png file — use as <img src="/api/v1/ai/gradcam/{scan_id}">
    """
    from pathlib import Path

    from core.exceptions import NotFoundException
    from routes.scan.service import get_scan

    scan = await get_scan(scan_id, tenant_db)
    ai_result = scan.get("ai_result") or {}
    gradcam_path = ai_result.get("gradcam_path")

    if not gradcam_path or not Path(gradcam_path).exists():
        raise NotFoundException("Grad-CAM heatmap not found. Run /ai/analyze first.")

    return FileResponse(
        path=gradcam_path,
        media_type="image/png",
        filename=f"{scan_id}_gradcam.png",
    )
