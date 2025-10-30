from fastapi import APIRouter
from psycopg2.extras import Json
from app.schemas.telemetry import TelemetryIn
from app.db.connection import get_db


router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.post("/")
def add_telemetry(data: TelemetryIn):
	with get_db() as cur:
		cur.execute(
			"""
			INSERT INTO telemetry (device_id, ts, data)
			VALUES (%s, to_timestamp(%s/1000.0), %s::jsonb);
			""",
			(data.device_id, data.ts, Json(data.data)),
		)
	return {"status": "ok"}


@router.get("/{device_id}")
def get_device_telemetry(device_id: str):
	with get_db() as cur:
		cur.execute(
			"SELECT * FROM telemetry WHERE device_id=%s ORDER BY ts DESC LIMIT 100;",
			(device_id,),
		)
		return cur.fetchall()


