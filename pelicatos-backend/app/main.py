from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from app.db.database import engine, Base
from app import models
from app.routers.auth import router as auth_router
from app.routers.content import public_router, router as content_router

def create_tables():
    Base.metadata.create_all(bind=engine, checkfirst=True)


def migrate_existing_tables():
    migrations = {
        "usuarios": {
            "foto_perfil": "ALTER TABLE usuarios ADD COLUMN foto_perfil VARCHAR(255) NULL",
            "biografia": "ALTER TABLE usuarios ADD COLUMN biografia TEXT NULL",
        },
        "aventuras": {
            "imagen_url": "ALTER TABLE aventuras ADD COLUMN imagen_url VARCHAR(255) NULL",
        },
        "perfiles": {
            "fondo_url": "ALTER TABLE perfiles ADD COLUMN fondo_url VARCHAR(255) NULL",
            "hero_image_url": "ALTER TABLE perfiles ADD COLUMN hero_image_url VARCHAR(255) NULL",
            "hero_eyebrow": "ALTER TABLE perfiles ADD COLUMN hero_eyebrow VARCHAR(160) NULL",
            "hero_titulo": "ALTER TABLE perfiles ADD COLUMN hero_titulo VARCHAR(180) NULL",
            "hero_descripcion": "ALTER TABLE perfiles ADD COLUMN hero_descripcion TEXT NULL",
            "facebook_url": "ALTER TABLE perfiles ADD COLUMN facebook_url VARCHAR(500) NULL",
            "instagram_url": "ALTER TABLE perfiles ADD COLUMN instagram_url VARCHAR(500) NULL",
            "tiktok_url": "ALTER TABLE perfiles ADD COLUMN tiktok_url VARCHAR(500) NULL",
            "youtube_url": "ALTER TABLE perfiles ADD COLUMN youtube_url VARCHAR(500) NULL",
            "footer_descripcion": "ALTER TABLE perfiles ADD COLUMN footer_descripcion VARCHAR(500) NULL",
            "copyright_texto": "ALTER TABLE perfiles ADD COLUMN copyright_texto VARCHAR(255) NULL",
        },
    }
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table_name, columns in migrations.items():
            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, statement in columns.items():
                if column_name not in existing_columns:
                    connection.execute(text(statement))


create_tables()
migrate_existing_tables()

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
app.include_router(public_router)
app.mount("/demo", StaticFiles(directory="app/static", html=True), name="demo")
app.mount("/media", StaticFiles(directory="app/static"), name="media")


@app.get("/")
def inicio():
    return {
        "mensaje": "Backend de Pelicatos TV funcionando correctamente"
    }