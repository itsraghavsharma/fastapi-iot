from fastapi import APIRouter
from passlib.hash import bcrypt
from app.db import crud
from app.schemas.user import UserBase


router = APIRouter(prefix="/user", tags=["User"])


@router.post("/")
def create_user(user: UserBase):
	user_data = {
		"username": user.username,
		"password_hash": bcrypt.hash(user.password),
		"org_id": user.org_id,
		"role": user.role,
	}
	return crud.create_record("user_master", user_data)


@router.get("/")
def list_users():
	return crud.get_all("user_master")


