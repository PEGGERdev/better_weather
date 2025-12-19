from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from data.mongo_service import MongoService
from routing.router import router_create
from data.dto import Weather, OSSD
import uvicorn

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = MongoService()


# Initiate routers for each entity
app.include_router(router_create(Weather, db.weather, "/weather", ["Wetter"]))
app.include_router(router_create(OSSD, db.ossd, "/ossd", ["OSSD"]))

@app.get("/")
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)