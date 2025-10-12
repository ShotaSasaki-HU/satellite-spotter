from fastapi import FastAPI
from app.routers import locations

app = FastAPI()

app.include_router(locations.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Satellite Spotter API!"}
