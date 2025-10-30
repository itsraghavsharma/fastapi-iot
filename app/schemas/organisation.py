from pydantic import BaseModel


class OrgBase(BaseModel):
	org_id: str
	org_name: str
	contact_email: str | None = None


class OrgCreate(OrgBase):
	pass


class OrgOut(OrgBase):
	pass


