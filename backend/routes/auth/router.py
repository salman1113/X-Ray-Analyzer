from fastapi import APIRouter, BackgroundTasks, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.database import get_master_db
from core.dependencies import get_current_user
from core.security import create_access_token
from routes.auth.schemas import (
    ForgotPasswordSchema,
    LoginSchema,
    RefreshTokenSchema,
    RegisterSchema,
    VerifyOTPSchema,
)
from routes.auth.service import (
    get_user_profile,
    login_user,
    refresh_access_token,
    register_user,
    verify_otp_and_activate,
)
from services.email import send_magic_link_email, send_otp_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
async def register(
    data: RegisterSchema,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    result = await register_user(
        email=data.email,
        password=data.password,
        role=data.role,
        hospital_name=data.hospital_name,
        invite_code=data.invite_code,
        db=db,
    )
    background_tasks.add_task(send_otp_email, data.email, result["otp_code"])
    return {
        "message": "OTP sent to email. Pending verification.",
        "subdomain": result["subdomain"],
        "tenant_url": result["tenant_url"],
    }


@router.post("/verify-otp")
async def verify_otp(
    data: VerifyOTPSchema,
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    result = await verify_otp_and_activate(data.email, data.otp, db)
    return {
        "message": "Registration complete",
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "has_passkey": result["has_passkey"],
        "subdomain": result.get("subdomain"),
        "tenant_url": result.get("tenant_url"),
    }


@router.post("/login")
async def login(
    data: LoginSchema,
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    result = await login_user(data.email, data.password, db)
    return {
        "message": "Login success",
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "has_passkey": result["has_passkey"],
        "subdomain": result.get("subdomain"),
        "tenant_url": result.get("tenant_url"),
    }


@router.post("/refresh")
async def refresh(
    data: RefreshTokenSchema,
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    result = await refresh_access_token(data.refresh_token, db)
    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
    }


@router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordSchema,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    user = await db.users.find_one({"email": data.email})
    if not user:
        return {"message": "If the account exists, a reset link was sent."}

    reset_token = create_access_token({"sub": data.email, "type": "magic_link"})
    background_tasks.add_task(send_magic_link_email, data.email, reset_token, data.origin)
    return {"message": "If the account exists, a reset link was sent."}


@router.get("/me")
async def me(
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    return await get_user_profile(user, db)
