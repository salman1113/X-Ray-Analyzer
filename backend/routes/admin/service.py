from motor.motor_asyncio import AsyncIOMotorDatabase


async def get_platform_stats(db: AsyncIOMotorDatabase) -> dict:
    """Get platform-wide statistics for superadmin dashboard."""
    total_users = await db.users.count_documents({})
    verified_users = await db.users.count_documents({"is_verified": True})
    total_hospitals = await db.hospitals.count_documents({})
    active_hospitals = await db.hospitals.count_documents({"is_active": True})

    return {
        "total_users": total_users,
        "verified_users": verified_users,
        "total_hospitals": total_hospitals,
        "active_hospitals": active_hospitals,
    }


async def get_dashboard_data(role: str, hospital_id: str | None, db: AsyncIOMotorDatabase) -> dict:
    """Returns role-specific dashboard data."""
    if role == "superadmin":
        stats = await get_platform_stats(db)
        hospitals_cursor = db.hospitals.find({})
        hospitals = await hospitals_cursor.to_list(1000)
        stats["hospitals"] = [
            {
                "id": h.get("hospital_id"),
                "name": h.get("name"),
                "plan": h.get("plan", "free"),
                "is_active": h.get("is_active", True),
            }
            for h in hospitals
        ]
        return {"type": "superadmin", **stats}

    elif role == "admin":
        doctors_cursor = db.users.find({"hospital_id": hospital_id, "role": "doctor"})
        doctors = await doctors_cursor.to_list(1000)
        return {
            "type": "admin",
            "roster": [
                {
                    "email": d["email"],
                    "is_verified": d.get("is_verified", False),
                    "has_passkey": bool(d.get("credential_id")),
                }
                for d in doctors
            ],
        }

    else:
        return {"type": "doctor", "message": "Ready to scan"}
