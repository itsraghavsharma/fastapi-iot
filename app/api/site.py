from fastapi import APIRouter
from app.db import crud
from app.schemas.site import SiteBase


router = APIRouter(prefix="/site", tags=["Site"])


@router.post("/")
def add_site(site: SiteBase):
	return crud.create_record("site_master", site.dict())


@router.get("/")
def get_sites():
	return crud.get_all("site_master")


