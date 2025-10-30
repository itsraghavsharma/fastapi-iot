from pydantic import BaseModel
from typing import Dict, Any


class TelemetryIn(BaseModel):
	device_id: str
	ts: int
	data: Dict[str, Any]


