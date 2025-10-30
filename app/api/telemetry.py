from fastapi import APIRouter, Query
from psycopg2.extras import Json
from app.schemas.telemetry import TelemetryIn
from app.db.connection import get_db
from typing import List


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



def _json_field_expr(field: str) -> str:
	# Safely extract numeric value from jsonb -> cast to double precision
	return f"(NULLIF((data->>'{field}'),'')::double precision) AS \"{field}\""


@router.get("/series/{device_id}")
def time_series(
	device_id: str,
	start_ms: int = Query(..., description="Start time in epoch ms"),
	end_ms: int = Query(..., description="End time in epoch ms"),
	bucket: str = Query("5 minutes", description="time_bucket interval, e.g. '5 minutes', '1 hour'"),
	fields: List[str] = Query(
		[
			"V_LL_AVG",
			"V_LN_AVG",
			"I_AVG",
			"P_TOTAL",
			"Q_TOTAL",
			"S_TOTAL",
			"PF_TOTAL",
			"Hz",
			"THD_VR",
			"THD_IR",
		],
		description="Telemetry JSON keys to include",
	),
):
	# Build select expressions for numeric fields with avg over bucket
	field_aggs = ",\n\t\t".join([f"avg({f'NULLIF((data->>\'{f}\'),\'\')::double precision'}) AS \"{f}\"" for f in fields])
	with get_db() as cur:
		cur.execute(
			f"""
			SELECT
				time_bucket(%s, ts) AS bucket,
				{field_aggs}
			FROM telemetry
			WHERE device_id=%s AND ts BETWEEN to_timestamp(%s/1000.0) AND to_timestamp(%s/1000.0)
			GROUP BY bucket
			ORDER BY bucket
			""",
			(bucket, device_id, start_ms, end_ms),
		)
		return cur.fetchall()


@router.get("/agg/{device_id}")
def aggregates(
	device_id: str,
	start_ms: int,
	end_ms: int,
	fields: List[str] = Query(["P_TOTAL", "Q_TOTAL", "S_TOTAL", "PF_TOTAL", "Hz"]),
):
	# Return avg, min, max for each requested field
	parts = []
	for f in fields:
		expr = f"NULLIF((data->>\'{f}\'),\'\')::double precision"
		parts.append(f"avg({expr}) AS \"{f}_avg\"")
		parts.append(f"min({expr}) AS \"{f}_min\"")
		parts.append(f"max({expr}) AS \"{f}_max\"")
	select_sql = ",\n\t\t".join(parts)
	with get_db() as cur:
		cur.execute(
			f"""
			SELECT {select_sql}
			FROM telemetry
			WHERE device_id=%s AND ts BETWEEN to_timestamp(%s/1000.0) AND to_timestamp(%s/1000.0)
			""",
			(device_id, start_ms, end_ms),
		)
		return cur.fetchone()


@router.get("/last/{device_id}")
def last_point(device_id: str):
	with get_db() as cur:
		cur.execute(
			"""
			SELECT device_id, extract(epoch from ts)*1000 AS ts_ms, data
			FROM telemetry
			WHERE device_id=%s
			ORDER BY ts DESC
			LIMIT 1
			""",
			(device_id,),
		)
		return cur.fetchone()


@router.get("/regression/{device_id}")
def linear_regression(
	device_id: str,
	start_ms: int,
	end_ms: int,
	x: str = Query("V_LL_AVG", description="Predictor field in JSON"),
	y: str = Query("P_TOTAL", description="Target field in JSON"),
):
	# Use PostgreSQL regr_* functions for simple linear regression
	xexpr = f"NULLIF((data->>\'{x}\'),\'\')::double precision"
	yexpr = f"NULLIF((data->>\'{y}\'),\'\')::double precision"
	with get_db() as cur:
		cur.execute(
			f"""
			SELECT
				regr_slope({yexpr}, {xexpr}) AS slope,
				regr_intercept({yexpr}, {xexpr}) AS intercept,
				regr_r2({yexpr}, {xexpr}) AS r2,
				count(*) AS n
			FROM telemetry
			WHERE device_id=%s AND ts BETWEEN to_timestamp(%s/1000.0) AND to_timestamp(%s/1000.0)
			""",
			(device_id, start_ms, end_ms),
		)
		return cur.fetchone()

