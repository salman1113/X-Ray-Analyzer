from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.database import get_master_db
from core.dependencies import require_admin
from routes.billing.service import get_usage

router = APIRouter(prefix="/billing", tags=["Billing & Usage"])


@router.get("/usage")
async def usage(
    user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    """Admin: get current usage stats for my hospital."""
    return await get_usage(user["tenant_id"], db)
