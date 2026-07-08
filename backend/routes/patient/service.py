import uuid
from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from core.exceptions import NotFoundException


async def create_patient(data: dict, user_email: str, db: AsyncIOMotorDatabase) -> dict:
    doc = {
        "patient_id": str(uuid.uuid4()),
        "name": data["name"],
        "age": data["age"],
        "gender": data["gender"],
        "contact": data.get("contact"),
        "medical_history": data.get("medical_history", []),
        "created_by": user_email,
        "created_at": datetime.now(UTC),
    }
    await db.patients.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def list_patients(db: AsyncIOMotorDatabase) -> list[dict]:
    cursor = db.patients.find({}, {"_id": 0})
    return await cursor.to_list(5000)


async def get_patient(patient_id: str, db: AsyncIOMotorDatabase) -> dict:
    patient = await db.patients.find_one({"patient_id": patient_id}, {"_id": 0})
    if not patient:
        raise NotFoundException("Patient")
    return patient


async def update_patient(patient_id: str, updates: dict, db: AsyncIOMotorDatabase) -> dict:
    clean = {k: v for k, v in updates.items() if v is not None}
    if not clean:
        return await get_patient(patient_id, db)
    result = await db.patients.update_one({"patient_id": patient_id}, {"$set": clean})
    if result.matched_count == 0:
        raise NotFoundException("Patient")
    return await get_patient(patient_id, db)


async def delete_patient(patient_id: str, db: AsyncIOMotorDatabase):
    result = await db.patients.delete_one({"patient_id": patient_id})
    if result.deleted_count == 0:
        raise NotFoundException("Patient")
