from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from core.settings import settings


class RegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["hospital", "doctor"] = "hospital"
    hospital_name: str | None = Field(default=None, max_length=120)
    invite_code: str | None = Field(default=None, max_length=20)


class LoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class VerifyOTPSchema(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ForgotPasswordSchema(BaseModel):
    email: EmailStr
    origin: str

    @field_validator("origin")
    @classmethod
    def validate_origin(cls, v: str) -> str:
        """Only allow origins under our own BASE_DOMAIN to prevent phishing."""
        from urllib.parse import urlparse

        parsed = urlparse(v)
        host = (parsed.hostname or "").lower()
        base = settings.BASE_DOMAIN.lower()
        if host != base and not host.endswith(f".{base}"):
            raise ValueError("Origin must be under the application domain")
        return v


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    has_passkey: bool = False
