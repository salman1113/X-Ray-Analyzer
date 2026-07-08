"""
Database connection and multi-tenant setup.

Architecture:
    - One shared "public" database for users, hospitals, audit logs
    - One separate database per hospital for their patients & scans

    public (ai_xray_master)     → users, hospitals, audit_logs
    tenant_<hospital_id>        → patients, scans
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from core.settings import settings

# Connect to MongoDB
client: AsyncIOMotorClient = AsyncIOMotorClient(settings.DATABASE_URL)

# Public database — shared across all tenants
master_db: AsyncIOMotorDatabase = client[settings.DB_NAME]


def get_master_db() -> AsyncIOMotorDatabase:
    """Returns the shared public database (users, hospitals, etc.)."""
    return master_db


def get_tenant_database(hospital_id: str) -> AsyncIOMotorDatabase:
    """
    Returns the isolated database for a specific hospital.
    Each hospital gets: tenant_<hospital_id>
    """
    return client[f"tenant_{hospital_id}"]


async def setup_tenant_database(hospital_id: str) -> AsyncIOMotorDatabase:
    """
    Create collections and indexes for a new tenant.
    Safe to call multiple times (indexes are idempotent).
    """
    db = get_tenant_database(hospital_id)

    # Ensure collections exist
    existing = set(await db.list_collection_names())
    if "patients" not in existing:
        await db.create_collection("patients")
    if "scans" not in existing:
        await db.create_collection("scans")

    # Create indexes
    await db.patients.create_index("patient_id", unique=True)
    await db.patients.create_index("created_by")
    await db.scans.create_index("scan_id", unique=True)
    await db.scans.create_index("patient_id")
    await db.scans.create_index("created_at")

    return db


async def check_connection() -> bool:
    """Check if MongoDB is reachable."""
    try:
        await client.admin.command("ping")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False
