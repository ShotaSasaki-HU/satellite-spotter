from fastapi import FastAPI
from app.routers import municipalities

app = FastAPI()

app.include_router(municipalities.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Satellite Spotter API!"}
