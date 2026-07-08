from pydantic import BaseModel, EmailStr


class PasskeyStartSchema(BaseModel):
    email: EmailStr


class PasskeyVerifySchema(BaseModel):
    email: EmailStr
    response: dict
