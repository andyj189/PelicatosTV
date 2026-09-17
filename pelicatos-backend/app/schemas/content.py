from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    biografia: str | None = Field(default=None, max_length=1000)


class SiteSettingsUpdate(BaseModel):
    nombre_mostrar: str = Field(min_length=2, max_length=100)
    descripcion: str | None = Field(default=None, max_length=1000)
    hero_eyebrow: str | None = Field(default=None, max_length=160)
    hero_titulo: str | None = Field(default=None, max_length=180)
    hero_descripcion: str | None = Field(default=None, max_length=1000)
    facebook_url: str | None = Field(default=None, max_length=500)
    instagram_url: str | None = Field(default=None, max_length=500)
    tiktok_url: str | None = Field(default=None, max_length=500)
    youtube_url: str | None = Field(default=None, max_length=500)
    footer_descripcion: str | None = Field(default=None, max_length=500)
    copyright_texto: str | None = Field(default=None, max_length=255)


class CategoryCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)


class AdventureCreate(BaseModel):
    titulo: str = Field(min_length=2, max_length=160)
    contenido: str = Field(min_length=1)
    ubicacion: str | None = Field(default=None, max_length=160)
    id_categoria: int | None = None


class AdventureUpdate(BaseModel):
    titulo: str = Field(min_length=2, max_length=160)
    contenido: str = Field(min_length=1)
    ubicacion: str | None = Field(default=None, max_length=160)
    id_categoria: int | None = None