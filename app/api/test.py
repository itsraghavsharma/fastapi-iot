from fastapi import APIRouter, Query
from typing import List, Any, Dict
from app.db.connection import get_db
from app.api.charts import ALLOWED_METRICS


router = APIRouter(prefix="/test", tags=["Test"])


def _fetch_devices(limit: int | None = None, only_device_id: str | None = None):
	with get_db() as cur:
		if only_device_id:
			cur.execute(
				"SELECT device_id FROM device_master WHERE device_id=%s;",
				(only_device_id,),
			)
		else:
			if limit is None:
				cur.execute("SELECT device_id FROM device_master ORDER BY device_id;")
			else:
				cur.execute(
					"SELECT device_id FROM device_master ORDER BY device_id LIMIT %s;",
					(limit,),
				)
		rows = cur.fetchall()
		return [r[0] for r in rows]


def _fetch_overview(device_id: str):
	selects = [
		"ts",
	] + [f"(data->>'{m}')::double precision AS {m}" for m in ALLOWED_METRICS]
	select_sql = ", ".join(selects)
	with get_db() as cur:
		cur.execute(
			f"""
			SELECT {select_sql}
			FROM telemetry
			WHERE device_id=%s
			ORDER BY ts DESC
			LIMIT 1;
			""",
			(device_id,),
		)
		return cur.fetchone()


def _fetch_timeseries(device_id: str, hours: int, limit: int):
	selects = [
		"ts",
	] + [f"(data->>'{m}')::double precision AS {m}" for m in ALLOWED_METRICS]
	select_sql = ", ".join(selects)
	with get_db() as cur:
		cur.execute(
			f"""
			SELECT {select_sql}
			FROM telemetry
			WHERE device_id=%s AND ts >= now() - (%s || ' hours')::interval
			ORDER BY ts ASC
			LIMIT %s;
			""",
			(device_id, str(hours), limit),
		)
		return cur.fetchall()


def _fetch_analytics(device_id: str, hours: int):
	aggs = []
	for m in ALLOWED_METRICS:
		aggs.append(f"avg((data->>'{m}')::double precision) AS {m}_avg")
		aggs.append(f"min((data->>'{m}')::double precision) AS {m}_min")
		aggs.append(f"max((data->>'{m}')::double precision) AS {m}_max")
	agg_sql = ", ".join(aggs)
	with get_db() as cur:
		cur.execute(
			f"""
			SELECT {agg_sql}
			FROM telemetry
			WHERE device_id=%s AND ts >= now() - (%s || ' hours')::interval;
			""",
			(device_id, str(hours)),
		)
		return cur.fetchone()


@router.get("/run")
def run(
	device_id: str | None = None,
	device_limit: int = 5,
	hours: int = 24,
	timeseries_limit: int = 50,
):
	device_ids = _fetch_devices(
		limit=None if device_id else device_limit,
		only_device_id=device_id,
	)
	results: Dict[str, Any] = {"devices_tested": device_ids, "results": {}}
	for did in device_ids:
		overview = _fetch_overview(did)
		ts = _fetch_timeseries(did, hours=hours, limit=timeseries_limit)
		analytics = _fetch_analytics(did, hours=hours)
		results["results"][did] = {
			"overview": overview,
			"timeseries_sample": ts,
			"analytics": analytics,
		}
	return results


