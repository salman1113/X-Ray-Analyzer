from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from core.dependencies import get_tenant_db, require_doctor
from core.exceptions import NotFoundException
from routes.scan.schemas import ScanCreateSchema
from routes.scan.service import create_scan, delete_scan, get_scan, list_scans

router = APIRouter(prefix="/scans", tags=["Scans"])


@router.post("/")
async def create(
    data: ScanCreateSchema,
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    return await create_scan(data.model_dump(), user["email"], tenant_db)


@router.get("/")
async def list_all(
    patient_id: str | None = Query(None),
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    return await list_scans(tenant_db, patient_id)


@router.get("/{scan_id}")
async def get_one(
    scan_id: str,
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    return await get_scan(scan_id, tenant_db)


@router.get("/{scan_id}/image")
async def get_image(
    scan_id: str,
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    scan = await get_scan(scan_id, tenant_db)
    image_path = scan.get("image_path")
    if not image_path or not Path(image_path).exists():
        raise NotFoundException("Scan image not found.")

    suffix = Path(image_path).suffix.lower()
    media_type = "image/png"
    if suffix in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif suffix == ".gif":
        media_type = "image/gif"

    return FileResponse(
        path=image_path,
        media_type=media_type,
        filename=Path(image_path).name,
    )


@router.post("/{scan_id}/upload")
async def upload_image(
    scan_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    import shutil
    from pathlib import Path

    tenant_id = user["tenant_id"]

    # Build a safe directory and write the file to disk
    upload_dir = Path("uploads") / tenant_id / scan_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = Path(file.filename).name  # strip any path components
    dest = upload_dir / safe_filename

    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    image_path = str(dest)
    await tenant_db.scans.update_one(
        {"scan_id": scan_id},
        {"$set": {"image_path": image_path, "status": "uploaded"}},
    )
    return {"message": "Image uploaded", "path": image_path}


@router.delete("/{scan_id}")
async def delete(
    scan_id: str,
    user: dict = Depends(require_doctor),
    tenant_db: AsyncIOMotorDatabase = Depends(get_tenant_db),
):
    await delete_scan(scan_id, tenant_db)
    return {"message": "Scan deleted"}
