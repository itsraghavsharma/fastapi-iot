from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.db.connection import get_db


router = APIRouter(prefix="/charts", tags=["Charts"])


ALLOWED_METRICS = {
	"thd_v_r",
	"pf_total",
	"frequency",
	"energy_kwh",
	"current_avg",
	"voltage_ll_avg",
	"active_power_total",
}


@router.get("/overview/{device_id}")
def overview(device_id: str):
	with get_db() as cur:
		cur.execute(
			"""
			SELECT ts,
				(data->>'thd_v_r')::double precision AS thd_v_r,
				(data->>'pf_total')::double precision AS pf_total,
				(data->>'frequency')::double precision AS frequency,
				(data->>'energy_kwh')::double precision AS energy_kwh,
				(data->>'current_avg')::double precision AS current_avg,
				(data->>'voltage_ll_avg')::double precision AS voltage_ll_avg,
				(data->>'active_power_total')::double precision AS active_power_total
			FROM telemetry
			WHERE device_id=%s
			ORDER BY ts DESC
			LIMIT 1;
			""",
			(device_id,),
		)
		row = cur.fetchone()
		if not row:
			raise HTTPException(status_code=404, detail="No telemetry found")
		return row


@router.get("/timeseries/{device_id}")
def timeseries(
	device_id: str,
	metrics: List[str] = Query(default=[
		"thd_v_r",
		"pf_total",
		"frequency",
		"energy_kwh",
		"current_avg",
		"voltage_ll_avg",
		"active_power_total",
	]),
	start_ms: int | None = None,
	end_ms: int | None = None,
	limit: int = 500,
):
	invalid = [m for m in metrics if m not in ALLOWED_METRICS]
	if invalid:
		raise HTTPException(status_code=400, detail=f"Invalid metrics: {', '.join(invalid)}")

	selects = ["ts"] + [f"(data->>'{m}')::double precision AS {m}" for m in metrics]
	select_sql = ", ".join(selects)
	where = ["device_id=%s"]
	params: list = [device_id]
	if start_ms is not None:
		where.append("ts >= to_timestamp(%s/1000.0)")
		params.append(start_ms)
	if end_ms is not None:
		where.append("ts <= to_timestamp(%s/1000.0)")
		params.append(end_ms)
	where_sql = " AND ".join(where)

	with get_db() as cur:
		cur.execute(
			f"SELECT {select_sql} FROM telemetry WHERE {where_sql} ORDER BY ts ASC LIMIT %s;",
			tuple(params + [limit]),
		)
		return cur.fetchall()


