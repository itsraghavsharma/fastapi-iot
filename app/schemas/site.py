from pydantic import BaseModel


class SiteBase(BaseModel):
	site_id: str
	org_id: str
	site_name: str
	location: str | None = None


