from motor.motor_asyncio import AsyncIOMotorDatabase

from core.exceptions import NotFoundException


def _user_to_dict(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "role": user.get("role", "doctor"),
        "is_verified": user.get("is_verified", False),
        "has_passkey": bool(user.get("credential_id")),
        "hospital_id": user.get("hospital_id"),
    }


async def list_users_in_tenant(hospital_id: str, db: AsyncIOMotorDatabase) -> list[dict]:
    """List all users belonging to a hospital."""
    cursor = db.users.find({"hospital_id": hospital_id})
    users = await cursor.to_list(1000)
    return [_user_to_dict(u) for u in users]


async def get_all_users(db: AsyncIOMotorDatabase) -> list[dict]:
    """Superadmin: list all users platform-wide."""
    cursor = db.users.find({})
    users = await cursor.to_list(5000)
    return [_user_to_dict(u) for u in users]


async def remove_user_from_tenant(email: str, hospital_id: str, db: AsyncIOMotorDatabase):
    """Admin: remove a doctor from the hospital."""
    result = await db.users.update_one(
        {"email": email, "hospital_id": hospital_id},
        {"$set": {"hospital_id": None, "role": "doctor"}},
    )
    if result.matched_count == 0:
        raise NotFoundException("User in this hospital")
