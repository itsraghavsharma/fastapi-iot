from pydantic import BaseModel


class DeviceBase(BaseModel):
	device_id: str
	plant_id: str
	device_name: str | None = None
	device_type: str | None = None
	model: str | None = None
	serial_no: str | None = None
	status: str | None = None
	installed_at: str | None = None


class DeviceCreate(DeviceBase):
	pass


class DeviceUpdate(BaseModel):
	plant_id: str | None = None
	device_name: str | None = None
	device_type: str | None = None
	model: str | None = None
	serial_no: str | None = None
	status: str | None = None
	installed_at: str | None = None


