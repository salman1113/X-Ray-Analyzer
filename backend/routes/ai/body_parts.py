"""
Body Part Registry — defines every supported X-ray scan type
and the medical conditions the AI can detect for each.

Each body part has:
  - label         : human-readable display name
  - conditions    : ordered list of class names the model predicts
                    (index 0 = normal/no finding baseline)
  - model_file    : filename of the fine-tuned model weights for this part
                    (placed in backend/routes/ai/models/)
  - description   : what the AI looks for

Adding a new body part:
  1. Add an entry here.
  2. Train/obtain a model checkpoint → save as models/<model_file>.
  3. The registry auto-registers it — no other code changes needed.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BodyPartConfig:
    label: str
    conditions: tuple[str, ...]  # frozen-safe (immutable sequence)
    model_file: str
    description: str


# ── Registry ──────────────────────────────────────────────────────────────────
_REGISTRY: dict[str, BodyPartConfig] = {
    # ── Chest ──────────────────────────────────────────────────────────────
    "chest": BodyPartConfig(
        label="Chest / Thorax",
        conditions=("Normal", "Pneumonia"),
        model_file="chest.pth",
        description=(
            "Analyzes lung fields, heart silhouette, and pleural spaces. "
            "Detects pneumonia, pleural effusion, and cardiomegaly."
        ),
    ),
    # ── Hand & Wrist ───────────────────────────────────────────────────────
    "hand": BodyPartConfig(
        label="Hand & Wrist",
        conditions=("Normal", "Fracture", "Arthritis", "Bone_Cyst"),
        model_file="hand.pth",
        description=(
            "Evaluates metacarpals, phalanges, and carpal bones. "
            "Detects fractures, osteoarthritis, and bone cysts."
        ),
    ),
    # ── Foot & Ankle ───────────────────────────────────────────────────────
    "foot": BodyPartConfig(
        label="Foot & Ankle",
        conditions=("Normal", "Fracture", "Arthritis", "Flat_Foot"),
        model_file="foot.pth",
        description=(
            "Assesses metatarsals, phalanges, and ankle mortise. "
            "Detects fractures, flat foot deformity, and arthritis."
        ),
    ),
    # ── Knee ───────────────────────────────────────────────────────────────
    "knee": BodyPartConfig(
        label="Knee",
        conditions=("Normal", "Osteoarthritis", "Fracture", "Effusion"),
        model_file="knee.pth",
        description=(
            "Examines femoral condyles, tibial plateau, and joint space. "
            "Detects osteoarthritis, fractures, and joint effusion."
        ),
    ),
    # ── Elbow ──────────────────────────────────────────────────────────────
    "elbow": BodyPartConfig(
        label="Elbow",
        conditions=("Normal", "Fracture", "Dislocation", "Arthritis"),
        model_file="elbow.pth",
        description=(
            "Evaluates distal humerus, radial head, and olecranon. "
            "Detects fractures, dislocations, and arthritis."
        ),
    ),
    # ── Shoulder ───────────────────────────────────────────────────────────
    "shoulder": BodyPartConfig(
        label="Shoulder",
        conditions=("Normal", "Fracture", "Dislocation", "AC_Joint_Separation"),
        model_file="shoulder.pth",
        description=(
            "Assesses glenohumeral joint, clavicle, and acromion. "
            "Detects fractures, dislocations, and AC joint injuries."
        ),
    ),
    # ── Spine (Lumbar / Cervical / Thoracic) ───────────────────────────────
    "spine": BodyPartConfig(
        label="Spine (Cervical / Thoracic / Lumbar)",
        conditions=(
            "Normal",
            "Scoliosis",
            "Compression_Fracture",
            "Disc_Narrowing",
            "Spondylolisthesis",
        ),
        model_file="spine.pth",
        description=(
            "Evaluates vertebral alignment, disc spaces, and bone density. "
            "Detects scoliosis, compression fractures, disc narrowing, and spondylolisthesis."
        ),
    ),
    # ── Hip & Pelvis ───────────────────────────────────────────────────────
    "hip": BodyPartConfig(
        label="Hip & Pelvis",
        conditions=("Normal", "Fracture", "Hip_Dysplasia", "Osteoarthritis", "Avascular_Necrosis"),
        model_file="hip.pth",
        description=(
            "Assesses femoral head, acetabulum, and pelvic ring. "
            "Detects fractures, hip dysplasia, arthritis, and avascular necrosis."
        ),
    ),
    # ── Forearm (Radius & Ulna) ────────────────────────────────────────────
    "forearm": BodyPartConfig(
        label="Forearm (Radius & Ulna)",
        conditions=("Normal", "Fracture", "Bowing"),
        model_file="forearm.pth",
        description=(
            "Evaluates radial and ulnar shafts. " "Detects fractures and bowing deformities."
        ),
    ),
    # ── Lower Leg (Tibia & Fibula) ─────────────────────────────────────────
    "leg": BodyPartConfig(
        label="Lower Leg (Tibia & Fibula)",
        conditions=("Normal", "Fracture", "Stress_Fracture", "Bone_Lesion"),
        model_file="leg.pth",
        description=(
            "Examines tibial and fibular shafts. "
            "Detects acute fractures, stress fractures, and bone lesions."
        ),
    ),
    # ── Skull ──────────────────────────────────────────────────────────────
    "skull": BodyPartConfig(
        label="Skull",
        conditions=("Normal", "Fracture", "Sinusitis"),
        model_file="skull.pth",
        description=(
            "Evaluates cranial vault and paranasal sinuses. "
            "Detects skull fractures and sinusitis."
        ),
    ),
    # ── Abdomen ────────────────────────────────────────────────────────────
    "abdomen": BodyPartConfig(
        label="Abdomen",
        conditions=("Normal", "Bowel_Obstruction", "Free_Air", "Calcification"),
        model_file="abdomen.pth",
        description=(
            "Assesses bowel gas pattern, solid organs, and calcifications. "
            "Detects bowel obstruction, free intraperitoneal air, and calculi."
        ),
    ),
}


def get_body_part(key: str) -> BodyPartConfig:
    """
    Retrieve config for a body part by its key.
    Raises KeyError with a helpful message if not found.
    """
    key = key.lower().strip()
    if key not in _REGISTRY:
        valid = ", ".join(sorted(_REGISTRY.keys()))
        raise KeyError(f"Unknown body part '{key}'. " f"Supported values: {valid}")
    return _REGISTRY[key]


def list_body_parts() -> dict[str, dict]:
    """Return all supported body parts as a JSON-serializable dict."""
    return {
        key: {
            "label": cfg.label,
            "conditions": cfg.conditions,
            "description": cfg.description,
        }
        for key, cfg in _REGISTRY.items()
    }


# All valid body part keys — useful for Pydantic validation
VALID_BODY_PARTS = list(_REGISTRY.keys())
