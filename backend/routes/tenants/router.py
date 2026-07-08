from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.database import get_master_db
from core.dependencies import get_current_user, require_admin, require_superadmin
from routes.tenants.schemas import TenantUpdateSchema
from routes.tenants.service import (
    deactivate_tenant,
    get_tenant,
    get_tenant_by_subdomain,
    list_all_tenants,
    regenerate_invite_code,
    update_tenant,
)

router = APIRouter(prefix="/tenants", tags=["Tenant Management"])


@router.get("/")
async def list_tenants(
    user: dict = Depends(require_superadmin),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    return await list_all_tenants(db)


@router.get("/mine")
async def get_my_tenant(
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    if not user.get("tenant_id"):
        return {"detail": "No tenant associated"}
    return await get_tenant(user["tenant_id"], db)


@router.get("/by-subdomain/{subdomain}")
async def lookup_by_subdomain(
    subdomain: str,
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    """
    Public — used by the SPA on a tenant subdomain to confirm the tenant
    exists before showing its login page. Returns a non-sensitive subset.
    """
    return await get_tenant_by_subdomain(subdomain, db)


@router.get("/{hospital_id}")
async def get_tenant_by_id(
    hospital_id: str,
    user: dict = Depends(require_superadmin),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    return await get_tenant(hospital_id, db)


@router.patch("/{hospital_id}")
async def update_tenant_route(
    hospital_id: str,
    data: TenantUpdateSchema,
    user: dict = Depends(require_superadmin),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    return await update_tenant(hospital_id, data.model_dump(exclude_none=True), db)


@router.post("/{hospital_id}/regenerate-invite")
async def regenerate_invite(
    hospital_id: str,
    user: dict = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    # IDOR guard: non-superadmin can only regenerate their own hospital's code
    if user["role"] != "superadmin" and user.get("tenant_id") != hospital_id:
        from core.exceptions import ForbiddenException

        raise ForbiddenException("You can only regenerate your own hospital's invite code")
    new_code = await regenerate_invite_code(hospital_id, db)
    return {"invite_code": new_code}


@router.delete("/{hospital_id}")
async def deactivate(
    hospital_id: str,
    user: dict = Depends(require_superadmin),
    db: AsyncIOMotorDatabase = Depends(get_master_db),
):
    await deactivate_tenant(hospital_id, db)
    return {"message": "Tenant deactivated"}
