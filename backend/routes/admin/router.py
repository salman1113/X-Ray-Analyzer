from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.database import get_master_db
from core.dependencies import get_current_user, require_superadmin
from routes.admin.service import get_dashboard_data, get_platform_stats

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get("/stats")
async def platform_stats(
    user: dict = Depends(require_superadmin),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    """Superadmin: platform-wide statistics."""
    return await get_platform_stats(db)


@router.get("/dashboard")
async def dashboard(
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    """Role-aware dashboard data."""
    return await get_dashboard_data(user["role"], user.get("tenant_id"), db)
