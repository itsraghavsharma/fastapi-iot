from fastapi import APIRouter, HTTPException
from app.db import crud
from app.db.connection import get_db
from app.schemas.device import DeviceCreate, DeviceUpdate


router = APIRouter(prefix="/device", tags=["Device"])


@router.post("/")
def create_device(device: DeviceCreate):
	try:
		return crud.create_record("device_master", device.dict())
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def list_devices():
	return crud.get_all("device_master")


@router.get("/{device_id}")
def get_device(device_id: str):
	row = crud.get_by_id("device_master", "device_id", device_id)
	if not row:
		raise HTTPException(status_code=404, detail="Device not found")
	return row


@router.put("/{device_id}")
def update_device(device_id: str, change: DeviceUpdate):
	data = {k: v for k, v in change.dict().items() if v is not None}
	if not data:
		raise HTTPException(status_code=400, detail="No fields to update")
	updated = crud.update_by_id("device_master", "device_id", device_id, data)
	if not updated:
		raise HTTPException(status_code=404, detail="Device not found")
	return updated


@router.delete("/{device_id}")
def delete_device(device_id: str):
	# best-effort delete
	crud.delete_by_id("device_master", "device_id", device_id)
	return {"status": "deleted"}


@router.get("/{device_id}/latest")
def get_device_latest(device_id: str):
	with get_db() as cur:
		cur.execute(
			"""
			SELECT ts, data
			FROM telemetry
			WHERE device_id=%s
			ORDER BY ts DESC
			LIMIT 1;
			""",
			(device_id,),
		)
		return cur.fetchone()


