from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    biografia: str | None = Field(default=None, max_length=1000)


class CategoryCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)


class AdventureCreate(BaseModel):
    titulo: str = Field(min_length=2, max_length=160)
    contenido: str = Field(min_length=1)
    ubicacion: str | None = Field(default=None, max_length=160)
    id_categoria: int | None = None