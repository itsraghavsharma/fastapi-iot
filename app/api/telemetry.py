from fastapi import APIRouter, HTTPException, Query, Depends
from psycopg2.extras import Json
from app.schemas.telemetry import TelemetryIn
from app.db.connection import get_db
from app.core.auth import get_current_user


router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.post("/")
def add_telemetry(data: TelemetryIn, current_user = Depends(get_current_user)):
	with get_db() as cur:
		# Ensure device belongs to user's org
		cur.execute(
			"""
			SELECT 1
			FROM device_master d
			JOIN plant_master p ON d.plant_id=p.plant_id
			JOIN site_master s ON p.site_id=s.site_id
			WHERE s.org_id=%s AND d.device_id=%s
			""",
			(current_user["org_id"], data.device_id),
		)
		if cur.fetchone() is None:
			raise HTTPException(status_code=403, detail="Device not in your organisation")
		cur.execute(
			"""
			INSERT INTO telemetry (device_id, ts, data)
			VALUES (%s, to_timestamp(%s/1000.0), %s::jsonb);
			""",
			(data.device_id, data.ts, Json(data.data)),
		)
	return {"status": "ok"}


@router.get("/")
def list_telemetry(limit: int = 100, current_user = Depends(get_current_user)):
    with get_db() as cur:
        cur.execute(
            """
            SELECT t.device_id, t.ts, t.data
            FROM telemetry t
            JOIN device_master d ON t.device_id=d.device_id
            JOIN plant_master p ON d.plant_id=p.plant_id
            JOIN site_master s ON p.site_id=s.site_id
            WHERE s.org_id=%s
            ORDER BY t.ts DESC
            LIMIT %s;
            """,
            (current_user["org_id"], limit),
        )
        return cur.fetchall()


@router.get("/{device_id}")
def get_device_telemetry(
    device_id: str,
    start_ms: int | None = None,
    end_ms: int | None = None,
    limit: int = 100,
    current_user = Depends(get_current_user),
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
            f"SELECT device_id, ts, data FROM telemetry WHERE {where_sql} ORDER BY ts DESC LIMIT %s;",
            tuple(params + [limit]),
        )
        return cur.fetchall()


@router.delete("/{device_id}/{ts_ms}")
def delete_telemetry(device_id: str, ts_ms: int, current_user = Depends(get_current_user)):
    with get_db() as cur:
        # Ensure device belongs to user's org
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
            "DELETE FROM telemetry WHERE device_id=%s AND ts=to_timestamp(%s/1000.0);",
            (device_id, ts_ms),
        )
    return {"status": "deleted"}


@router.put("/{device_id}/{ts_ms}")
def update_telemetry(device_id: str, ts_ms: int, payload: dict, current_user = Depends(get_current_user)):
    if not payload:
        raise HTTPException(status_code=400, detail="No data provided")
    with get_db() as cur:
        # Ensure device belongs to user's org
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


