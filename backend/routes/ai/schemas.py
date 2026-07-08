from pydantic import BaseModel, field_validator

from routes.ai.body_parts import VALID_BODY_PARTS


class AnalyzeRequest(BaseModel):
    scan_id: str
    body_part: str = "chest"  # defaults to chest for backwards compatibility

    @field_validator("body_part")
    @classmethod
    def validate_body_part(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_BODY_PARTS:
            raise ValueError(
                f"Invalid body_part '{v}'. "
                f"Supported values: {', '.join(sorted(VALID_BODY_PARTS))}"
            )
        return v


class AIResult(BaseModel):
    body_part: str
    body_part_label: str  # e.g. "Knee", "Chest / Thorax"
    prediction: str  # e.g. "Osteoarthritis", "Normal"
    confidence: float  # 0.0 – 1.0
    probabilities: dict[str, float]  # {"Normal": 0.08, "Osteoarthritis": 0.87, ...}
    gradcam_path: str | None = None
    rag_explanation: str | None = None


class AnalyzeResponse(BaseModel):
    scan_id: str
    status: str = "analyzed"
    ai_result: AIResult | None = None


class BodyPartInfo(BaseModel):
    key: str
    label: str
    conditions: list[str]
    description: str
