from fastapi import FastAPI
from app.api import organisation, site, plant, telemetry, user


app = FastAPI(title="Industrial IoT API")

app.include_router(organisation.router)
app.include_router(site.router)
app.include_router(plant.router)
app.include_router(user.router)
app.include_router(telemetry.router)


