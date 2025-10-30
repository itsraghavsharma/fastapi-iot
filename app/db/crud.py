from app.db.connection import get_db


def create_record(table: str, data: dict):
	with get_db() as cur:
		cols = ', '.join(data.keys())
		vals = ', '.join(['%s'] * len(data))
		cur.execute(
			f"INSERT INTO {table} ({cols}) VALUES ({vals}) RETURNING *;",
			tuple(data.values()),
		)
		return cur.fetchone()


def get_all(table: str):
	with get_db() as cur:
		cur.execute(f"SELECT * FROM {table};")
		return cur.fetchall()


def get_by_id(table: str, key: str, value):
	with get_db() as cur:
		cur.execute(f"SELECT * FROM {table} WHERE {key}=%s;", (value,))
		return cur.fetchone()


def delete_by_id(table: str, key: str, value):
	with get_db() as cur:
		cur.execute(f"DELETE FROM {table} WHERE {key}=%s;", (value,))


def update_by_id(table: str, key: str, value, data: dict):
	with get_db() as cur:
		set_clause = ', '.join([f"{k}=%s" for k in data.keys()])
		params = list(data.values()) + [value]
		cur.execute(
			f"UPDATE {table} SET {set_clause} WHERE {key}=%s RETURNING *;",
			tuple(params),
		)
		return cur.fetchone()


