import uuid

from motor.motor_asyncio import AsyncIOMotorDatabase

from core.exceptions import BadRequestException, NotFoundException
from core.tenancy import build_tenant_url


def _serialize(h: dict) -> dict:
    sub = h.get("subdomain")
    return {
        "hospital_id": h.get("hospital_id"),
        "name": h.get("name"),
        "subdomain": sub,
        "tenant_url": build_tenant_url(sub) if sub else None,
        "invite_code": h.get("invite_code"),
        "plan": h.get("plan", "free"),
        "max_users": h.get("max_users", 5),
        "max_scans_per_month": h.get("max_scans_per_month", 100),
        "is_active": h.get("is_active", True),
    }


def _serialize_public(h: dict) -> dict:
    """Subset safe for unauthenticated subdomain lookup."""
    sub = h.get("subdomain")
    return {
        "hospital_id": h.get("hospital_id"),
        "name": h.get("name"),
        "subdomain": sub,
        "tenant_url": build_tenant_url(sub) if sub else None,
        "is_active": h.get("is_active", True),
    }


async def list_all_tenants(db: AsyncIOMotorDatabase) -> list[dict]:
    cursor = db.hospitals.find({})
    hospitals = await cursor.to_list(1000)
    return [_serialize(h) for h in hospitals]


async def get_tenant(hospital_id: str, db: AsyncIOMotorDatabase) -> dict:
    hospital = await db.hospitals.find_one({"hospital_id": hospital_id})
    if not hospital:
        raise NotFoundException("Hospital")
    return _serialize(hospital)


async def get_tenant_by_subdomain(subdomain: str, db: AsyncIOMotorDatabase) -> dict:
    hospital = await db.hospitals.find_one({"subdomain": subdomain.lower()})
    if not hospital:
        raise NotFoundException("Hospital")
    return _serialize_public(hospital)


async def update_tenant(hospital_id: str, updates: dict, db: AsyncIOMotorDatabase) -> dict:
    clean = {k: v for k, v in updates.items() if v is not None}
    if not clean:
        raise BadRequestException("No fields to update")
    result = await db.hospitals.update_one({"hospital_id": hospital_id}, {"$set": clean})
    if result.matched_count == 0:
        raise NotFoundException("Hospital")
    return await get_tenant(hospital_id, db)


async def regenerate_invite_code(hospital_id: str, db: AsyncIOMotorDatabase) -> str:
    new_code = str(uuid.uuid4())[:8].upper()
    result = await db.hospitals.update_one(
        {"hospital_id": hospital_id}, {"$set": {"invite_code": new_code}}
    )
    if result.matched_count == 0:
        raise NotFoundException("Hospital")
    return new_code


async def deactivate_tenant(hospital_id: str, db: AsyncIOMotorDatabase):
    result = await db.hospitals.update_one(
        {"hospital_id": hospital_id}, {"$set": {"is_active": False}}
    )
    if result.matched_count == 0:
        raise NotFoundException("Hospital")
