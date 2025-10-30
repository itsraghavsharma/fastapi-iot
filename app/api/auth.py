from datetime import datetime, timedelta, timezone
import os
import jwt
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from passlib.hash import pbkdf2_sha256
from app.db.connection import get_db


router = APIRouter(prefix="/auth", tags=["Auth"])


def _create_access_token(payload: dict, expires_delta: timedelta | None = None) -> str:
	expire = datetime.now(tz=timezone.utc) + (expires_delta or timedelta(hours=8))
	to_encode = {**payload, "exp": expire}
	secret = os.getenv("TOKEN_SECRET", "dev-secret-change-me")
	algorithm = os.getenv("TOKEN_ALGO", "HS256")
	return jwt.encode(to_encode, secret, algorithm=algorithm)


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
	# username/password form fields expected
	with get_db() as cur:
		cur.execute(
			"SELECT username, password, org_id, role FROM user_master WHERE username=%s;",
			(form_data.username,),
		)
		user = cur.fetchone()
		if not user or not pbkdf2_sha256.verify(form_data.password, user["password"]):
			raise HTTPException(status_code=400, detail="Incorrect username or password")

		token = _create_access_token(
			{"sub": user["username"], "org_id": user["org_id"], "role": user["role"]}
		)
		return {"access_token": token, "token_type": "bearer"}


