from fastapi import APIRouter, Body, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.database import get_master_db
from routes.passkey.service import (
    start_login,
    start_registration,
    verify_login,
    verify_registration,
)

router = APIRouter(prefix="/auth/passkey", tags=["Passkey Authentication"])


@router.post("/register/start")
async def passkey_register_start(
    email: str,
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    return await start_registration(email, db)


@router.post("/register/verify")
async def passkey_register_verify(
    email: str,
    response: dict = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    result = await verify_registration(email, response, db)
    return {
        "message": "Passkey registered successfully",
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
    }


@router.post("/login/start")
async def passkey_login_start(
    email: str,
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    return await start_login(email, db)


@router.post("/login/verify")
async def passkey_login_verify(
    email: str,
    response: dict = Body(...),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    result = await verify_login(email, response, db)
    return {
        "message": "Passkey login success",
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
    }
