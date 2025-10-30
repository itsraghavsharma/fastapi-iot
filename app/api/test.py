from fastapi import APIRouter, Query, Depends
from typing import List, Any, Dict
from app.db.connection import get_db
from app.api.charts import ALLOWED_METRICS
from app.core.auth import get_current_user


router = APIRouter(prefix="/test", tags=["Test"])


def _fetch_devices(org_id: str, limit: int | None = None, only_device_id: str | None = None):
	with get_db() as cur:
		if only_device_id:
			cur.execute(
				"""
				SELECT d.device_id
				FROM device_master d
				JOIN plant_master p ON d.plant_id=p.plant_id
				JOIN site_master s ON p.site_id=s.site_id
				WHERE s.org_id=%s AND d.device_id=%s
				ORDER BY d.device_id
				""",
				(org_id, only_device_id),
			)
		else:
			if limit is None:
				cur.execute(
					"""
					SELECT d.device_id
					FROM device_master d
					JOIN plant_master p ON d.plant_id=p.plant_id
					JOIN site_master s ON p.site_id=s.site_id
					WHERE s.org_id=%s
					ORDER BY d.device_id
					""",
					(org_id,),
				)
			else:
				cur.execute(
					"""
					SELECT d.device_id
					FROM device_master d
					JOIN plant_master p ON d.plant_id=p.plant_id
					JOIN site_master s ON p.site_id=s.site_id
					WHERE s.org_id=%s
					ORDER BY d.device_id
					LIMIT %s
					""",
					(org_id, limit),
				)
		rows = cur.fetchall()
		return [r["device_id"] for r in rows]


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
    current_user: Dict[str, Any] = Depends(get_current_user),
):
	device_ids = _fetch_devices(
		org_id=current_user["org_id"],
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


