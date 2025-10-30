from fastapi import APIRouter, HTTPException
from app.db import crud
from app.schemas.organisation import OrgCreate


router = APIRouter(prefix="/organisation", tags=["Organisation"])


@router.post("/")
def create_org(org: OrgCreate):
	try:
		return crud.create_record("organisation_master", org.dict())
	except Exception as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def list_orgs():
	return crud.get_all("organisation_master")


