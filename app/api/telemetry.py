from fastapi import APIRouter, HTTPException, Query
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


@router.get("/")
def list_telemetry(limit: int = 100):
    with get_db() as cur:
        cur.execute(
            "SELECT device_id, ts, data FROM telemetry ORDER BY ts DESC LIMIT %s;",
            (limit,),
        )
        return cur.fetchall()


@router.get("/{device_id}")
def get_device_telemetry(
    device_id: str,
    start_ms: int | None = None,
    end_ms: int | None = None,
    limit: int = 100,
):
    params = [device_id]
    where = ["device_id=%s"]
    if start_ms is not None:
        where.append("ts >= to_timestamp(%s/1000.0)")
        params.append(start_ms)
    if end_ms is not None:
        where.append("ts <= to_timestamp(%s/1000.0)")
        params.append(end_ms)
    where_sql = " AND ".join(where)
    with get_db() as cur:
        cur.execute(
            f"SELECT device_id, ts, data FROM telemetry WHERE {where_sql} ORDER BY ts DESC LIMIT %s;",
            tuple(params + [limit]),
        )
        return cur.fetchall()


@router.delete("/{device_id}/{ts_ms}")
def delete_telemetry(device_id: str, ts_ms: int):
    with get_db() as cur:
        cur.execute(
            "DELETE FROM telemetry WHERE device_id=%s AND ts=to_timestamp(%s/1000.0);",
            (device_id, ts_ms),
        )
    return {"status": "deleted"}


@router.put("/{device_id}/{ts_ms}")
def update_telemetry(device_id: str, ts_ms: int, payload: dict):
    if not payload:
        raise HTTPException(status_code=400, detail="No data provided")
    with get_db() as cur:
        cur.execute(
            """
            UPDATE telemetry
            SET data = data || %s::jsonb
            WHERE device_id=%s AND ts=to_timestamp(%s/1000.0)
            RETURNING device_id, ts, data;
            """,
            (Json(payload), device_id, ts_ms),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Telemetry not found")
        return row


