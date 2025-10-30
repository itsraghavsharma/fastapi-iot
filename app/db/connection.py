import os
import psycopg2
from contextlib import contextmanager


def _get_connection():
	return psycopg2.connect(
		host=os.getenv("DB_HOST", "localhost"),
		dbname=os.getenv("DB_NAME"),
		user=os.getenv("DB_USER"),
		password=os.getenv("DB_PASSWORD"),
	)


@contextmanager
def get_db():
	conn = _get_connection()
	cur = conn.cursor()
	try:
		yield cur
		conn.commit()
	except Exception:
		conn.rollback()
		raise
	finally:
		cur.close()
		conn.close()


