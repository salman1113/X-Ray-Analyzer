from pydantic import BaseModel


class PlanSchema(BaseModel):
    name: str  # free | basic | professional | enterprise
    max_users: int
    max_scans_per_month: int
    price_monthly: float = 0.0
    features: list[str] = []


class UsageOut(BaseModel):
    tenant_id: str
    current_month_scans: int
    max_scans_per_month: int
    current_users: int
    max_users: int
    plan: str
