from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    email: EmailStr
    role: str
    is_verified: bool
    has_passkey: bool
    hospital_id: str | None = None


class UserUpdateSchema(BaseModel):
    role: str | None = None
    is_active: bool | None = None
