# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import locations, recommendations, forecasts, trajectories, stars
from app.core.config import Settings, get_settings

settings: Settings = get_settings()
LOCAL_IP_ADDRESS = settings.LOCAL_IP_ADDRESS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # アクセスを許可するフロントエンドのURLリスト
    allow_origins=[
        "http://localhost:3000",
        f"http://{LOCAL_IP_ADDRESS}:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"], # GET, POST, PUT, DELETEなど全て許可
    allow_headers=["*"], # 全てのHTTPヘッダーを許可
)

app.include_router(locations.router)
app.include_router(recommendations.router)
app.include_router(forecasts.router)
app.include_router(trajectories.router)
app.include_router(stars.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Satellite Spotter API!"}
