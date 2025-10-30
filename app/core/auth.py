import os
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
	secret = os.getenv("TOKEN_SECRET", "dev-secret-change-me")
	algorithms = [os.getenv("TOKEN_ALGO", "HS256")]
	try:
		payload = jwt.decode(token, secret, algorithms=algorithms)
		username: str | None = payload.get("sub")
		org_id: str | None = payload.get("org_id")
		role: str | None = payload.get("role")
		if not username or not org_id:
			raise HTTPException(status_code=401, detail="Invalid token payload")
		return {"username": username, "org_id": org_id, "role": role}
	except jwt.ExpiredSignatureError:
		raise HTTPException(status_code=401, detail="Token expired")
	except jwt.InvalidTokenError:
		raise HTTPException(status_code=401, detail="Invalid token")


