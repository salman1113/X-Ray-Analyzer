from pydantic import BaseModel, field_validator

from routes.ai.body_parts import VALID_BODY_PARTS


class ScanCreateSchema(BaseModel):
    patient_id: str
    body_part: str = "chest"  # which part of the body is being scanned
    scan_type: str = "xray"  # xray | mri | ct (future)
    notes: str | None = None

    @field_validator("body_part")
    @classmethod
    def validate_body_part(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_BODY_PARTS:
            raise ValueError(
                f"Invalid body_part '{v}'. " f"Supported: {', '.join(sorted(VALID_BODY_PARTS))}"
            )
        return v


class ScanOut(BaseModel):
    scan_id: str
    patient_id: str
    body_part: str
    scan_type: str
    status: str  # uploaded | processing | analyzed | failed
    image_path: str | None = None
    ai_result: dict | None = None
    notes: str | None = None
    created_by: str


class AIResultSchema(BaseModel):
    body_part: str
    body_part_label: str
    prediction: str
    confidence: float
    probabilities: dict
    gradcam_path: str | None = None
    rag_explanation: str | None = None
