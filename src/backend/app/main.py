# app/main.py
from fastapi import FastAPI
from app.routers import locations, spots

app = FastAPI()

app.include_router(locations.router)
app.include_router(spots.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Satellite Spotter API!"}
