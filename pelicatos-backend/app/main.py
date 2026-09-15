from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.db.database import engine, Base
from app import models
from app.routers.auth import router as auth_router
from app.routers.content import router as content_router

def create_tables():
    Base.metadata.create_all(bind=engine, checkfirst=True)


create_tables()

app = FastAPI(
    title="Pelicatos TV API",
    description="Backend para gestionar usuarios y experiencias",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(content_router)
app.mount("/demo", StaticFiles(directory="app/static", html=True), name="demo")
app.mount("/media", StaticFiles(directory="app/static"), name="media")


@app.get("/")
def inicio():
    return {
        "mensaje": "Backend de Pelicatos TV funcionando correctamente"
    }