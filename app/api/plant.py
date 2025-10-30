from fastapi import APIRouter
from app.db import crud
from app.schemas.plant import PlantBase


router = APIRouter(prefix="/plant", tags=["Plant"])


@router.post("/")
def add_plant(plant: PlantBase):
	return crud.create_record("plant_master", plant.dict())


@router.get("/")
def get_plants():
	return crud.get_all("plant_master")


