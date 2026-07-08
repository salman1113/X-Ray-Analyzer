import uuid
from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from core.exceptions import NotFoundException


async def create_scan(data: dict, user_email: str, db: AsyncIOMotorDatabase) -> dict:
    doc = {
        "scan_id": str(uuid.uuid4()),
        "patient_id": data["patient_id"],
        "body_part": data.get("body_part", "chest"),  # e.g. chest | knee | hand | spine
        "scan_type": data.get("scan_type", "xray"),
        "status": "pending",  # pending → uploaded → processing → analyzed
        "image_path": None,
        "ai_result": None,
        "notes": data.get("notes"),
        "created_by": user_email,
        "reviewed_by": None,
        "created_at": datetime.now(UTC),
    }
    await db.scans.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def list_scans(db: AsyncIOMotorDatabase, patient_id: str | None = None) -> list[dict]:
    query = {"patient_id": patient_id} if patient_id else {}
    cursor = db.scans.find(query, {"_id": 0})
    return await cursor.to_list(5000)


async def get_scan(scan_id: str, db: AsyncIOMotorDatabase) -> dict:
    scan = await db.scans.find_one({"scan_id": scan_id}, {"_id": 0})
    if not scan:
        raise NotFoundException("Scan")
    return scan


async def update_scan_status(scan_id: str, status: str, db: AsyncIOMotorDatabase) -> dict:
    result = await db.scans.update_one({"scan_id": scan_id}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise NotFoundException("Scan")
    return await get_scan(scan_id, db)


async def save_ai_result(scan_id: str, ai_result: dict, db: AsyncIOMotorDatabase) -> dict:
    result = await db.scans.update_one(
        {"scan_id": scan_id},
        {"$set": {"ai_result": ai_result, "status": "analyzed"}},
    )
    if result.matched_count == 0:
        raise NotFoundException("Scan")
    return await get_scan(scan_id, db)


async def delete_scan(scan_id: str, db: AsyncIOMotorDatabase):
    result = await db.scans.delete_one({"scan_id": scan_id})
    if result.deleted_count == 0:
        raise NotFoundException("Scan")
