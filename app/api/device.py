from fastapi import APIRouter, HTTPException, Depends
from app.db import crud
from app.db.connection import get_db
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.core.auth import get_current_user


router = APIRouter(prefix="/device", tags=["Device"])


@router.post("/")
def create_device(device: DeviceCreate):
	try:
		return crud.create_record("device_master", device.dict())
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def list_devices(current_user = Depends(get_current_user)):
	with get_db() as cur:
		cur.execute(
			"""
			SELECT d.*
			FROM device_master d
			JOIN plant_master p ON d.plant_id=p.plant_id
			JOIN site_master s ON p.site_id=s.site_id
			WHERE s.org_id=%s
			ORDER BY d.device_id
			""",
			(current_user["org_id"],),
		)
		return cur.fetchall()


@router.get("/{device_id}")
def get_device(device_id: str, current_user = Depends(get_current_user)):
	with get_db() as cur:
		cur.execute(
			"""
			SELECT d.*
			FROM device_master d
			JOIN plant_master p ON d.plant_id=p.plant_id
			JOIN site_master s ON p.site_id=s.site_id
			WHERE s.org_id=%s AND d.device_id=%s
			""",
			(current_user["org_id"], device_id),
		)
		row = cur.fetchone()
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
def get_device_latest(device_id: str, current_user = Depends(get_current_user)):
	with get_db() as cur:
		cur.execute(
			"""
			SELECT 1
			FROM device_master d
			JOIN plant_master p ON d.plant_id=p.plant_id
			JOIN site_master s ON p.site_id=s.site_id
			WHERE s.org_id=%s AND d.device_id=%s
			""",
			(current_user["org_id"], device_id),
		)
		if cur.fetchone() is None:
			raise HTTPException(status_code=403, detail="Device not in your organisation")
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


