from pydantic import BaseModel


class TenantOut(BaseModel):
    hospital_id: str
    name: str
    subdomain: str | None = None
    tenant_url: str | None = None
    invite_code: str | None = None
    plan: str = "free"
    max_users: int = 5
    max_scans_per_month: int = 100
    is_active: bool = True


class TenantPublicOut(BaseModel):
    """Safe-to-expose subset for the public subdomain lookup endpoint."""

    hospital_id: str
    name: str
    subdomain: str
    tenant_url: str
    is_active: bool


class TenantUpdateSchema(BaseModel):
    name: str | None = None
    plan: str | None = None
    max_users: int | None = None
    max_scans_per_month: int | None = None
    is_active: bool | None = None
