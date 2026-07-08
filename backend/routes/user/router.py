from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.database import get_master_db
from core.dependencies import require_admin, require_superadmin
from routes.user.service import (
    get_all_users,
    list_users_in_tenant,
    remove_user_from_tenant,
)

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("/")
async def list_platform_users(
    user: dict = Depends(require_superadmin),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    """Superadmin: list all users."""
    return await get_all_users(db)


@router.get("/roster")
async def list_tenant_users(
    user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    """Admin: list doctors in my hospital."""
    return await list_users_in_tenant(user["tenant_id"], db)


@router.delete("/roster/{email}")
async def remove_doctor(
    email: str,
    user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    """Admin: remove a doctor from the hospital."""
    await remove_user_from_tenant(email, user["tenant_id"], db)
    return {"message": f"{email} removed from hospital"}
