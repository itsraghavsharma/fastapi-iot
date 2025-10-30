from fastapi import APIRouter
from app.db import crud
from app.schemas.device import DeviceBase


router = APIRouter(prefix="/device", tags=["Device"])


@router.post("/")
def add_device(device: DeviceBase):
	return crud.create_record("device_master", device.dict())


@router.get("/")
def list_devices():
	return crud.get_all("device_master")


@router.get("/{device_id}")
def get_device(device_id: str):
	return crud.get_by_id("device_master", "device_id", device_id)


@router.delete("/{device_id}")
def delete_device(device_id: str):
	crud.delete_by_id("device_master", "device_id", device_id)
	return {"status": "deleted"}



