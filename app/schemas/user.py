from pydantic import BaseModel


class UserBase(BaseModel):
	username: str
	password: str
	org_id: str
	role: str = "operator"


