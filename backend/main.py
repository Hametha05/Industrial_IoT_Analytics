from fastapi import FastAPI

from backend.routes.machine_routes import router as machine_router
from backend.routes.analytics_routes import router as analytics_router

app = FastAPI(title="Industrial IoT Analytics")

@app.get("/")
def home():
    return {
        "message": "Industrial IoT API Running"
}


app.include_router(
    machine_router,
    prefix="/machines",
    tags=["Machines"]
)


app.include_router(
    analytics_router,
    prefix="/machines",
    tags=["Analytics"]
)