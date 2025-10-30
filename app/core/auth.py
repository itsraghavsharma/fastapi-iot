import os
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.db.connection import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
	secret = os.getenv("TOKEN_SECRET", "dev-secret-change-me")
	algorithms = [os.getenv("TOKEN_ALGO", "HS256")]
	try:
		payload = jwt.decode(token, secret, algorithms=algorithms)
		username: str | None = payload.get("sub")
		if not username:
			raise HTTPException(status_code=401, detail="Invalid token payload")
		# Always read org_id and role from DB to prevent token org spoofing
		with get_db() as cur:
			cur.execute(
				"SELECT org_id, role FROM user_master WHERE username=%s;",
				(username,),
			)
			row = cur.fetchone()
			if not row:
				raise HTTPException(status_code=401, detail="User not found")
			return {"username": username, "org_id": row["org_id"], "role": row["role"]}
	except jwt.ExpiredSignatureError:
		raise HTTPException(status_code=401, detail="Token expired")
	except jwt.InvalidTokenError:
		raise HTTPException(status_code=401, detail="Invalid token")


