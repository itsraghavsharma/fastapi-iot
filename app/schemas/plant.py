from pydantic import BaseModel


class PlantBase(BaseModel):
	plant_id: str
	site_id: str
	plant_name: str


