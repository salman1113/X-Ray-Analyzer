from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from core.database import get_tenant_database
from core.exceptions import PlanLimitExceededException

PLANS = {
    "free": {"max_users": 5, "max_scans_per_month": 100, "price": 0},
    "basic": {"max_users": 20, "max_scans_per_month": 1000, "price": 49},
    "professional": {"max_users": 100, "max_scans_per_month": 10000, "price": 199},
    "enterprise": {"max_users": 999999, "max_scans_per_month": 999999, "price": 0},
}


async def get_usage(tenant_id: str, master_db: AsyncIOMotorDatabase) -> dict:
    """Get current usage stats for a tenant."""
    hospital = await master_db.hospitals.find_one({"hospital_id": tenant_id})
    if not hospital:
        return {}

    user_count = await master_db.users.count_documents({"hospital_id": tenant_id})

    tenant_db = get_tenant_database(tenant_id)
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    scan_count = await tenant_db.scans.count_documents({"created_at": {"$gte": month_start}})

    return {
        "tenant_id": tenant_id,
        "current_month_scans": scan_count,
        "max_scans_per_month": hospital.get("max_scans_per_month", 100),
        "current_users": user_count,
        "max_users": hospital.get("max_users", 5),
        "plan": hospital.get("plan", "free"),
    }


async def check_scan_limit(tenant_id: str, master_db: AsyncIOMotorDatabase):
    usage = await get_usage(tenant_id, master_db)
    if usage["current_month_scans"] >= usage["max_scans_per_month"]:
        raise PlanLimitExceededException(
            f"Monthly scan limit ({usage['max_scans_per_month']}) reached."
        )


async def check_user_limit(tenant_id: str, master_db: AsyncIOMotorDatabase):
    usage = await get_usage(tenant_id, master_db)
    if usage["current_users"] >= usage["max_users"]:
        raise PlanLimitExceededException(f"User limit ({usage['max_users']}) reached.")
