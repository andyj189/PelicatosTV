from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.db.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(
        String(150),
        unique=True,
        nullable=False,
        index=True
    )
    password_hash = Column(String(255), nullable=False)
    foto_perfil = Column(String(255), nullable=True)
    biografia = Column(Text, nullable=True)
    fecha_registro = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class Perfil(Base):
    __tablename__ = "perfiles"
    id_perfil = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    nombre_mostrar = Column(String(100), nullable=True)
    descripcion = Column(Text, nullable=True)
    foto_perfil = Column(String(255), nullable=True)
    logo = Column(String(255), nullable=True)
    biografia = Column(Text, nullable=True)
    fondo_url = Column(String(255), nullable=True)
    hero_image_url = Column(String(255), nullable=True)
    hero_eyebrow = Column(String(160), nullable=True)
    hero_titulo = Column(String(180), nullable=True)
    hero_descripcion = Column(Text, nullable=True)
    facebook_url = Column(String(500), nullable=True)
    instagram_url = Column(String(500), nullable=True)
    tiktok_url = Column(String(500), nullable=True)
    youtube_url = Column(String(500), nullable=True)
    footer_descripcion = Column(String(500), nullable=True)
    copyright_texto = Column(String(255), nullable=True)


class Categoria(Base):
    __tablename__ = "categorias"
    id_categoria = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(80), nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False, index=True)


class Aventura(Base):
    __tablename__ = "aventuras"
    id_aventura = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(160), nullable=False)
    contenido = Column(Text, nullable=False)
    ubicacion = Column(String(160), nullable=True)
    imagen_url = Column(String(255), nullable=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False, index=True)
    id_categoria = Column(Integer, ForeignKey("categorias.id_categoria", ondelete="SET NULL"), nullable=True, index=True)


class Foto(Base):
    __tablename__ = "fotos"
    id_foto = Column(Integer, primary_key=True, index=True)
    nombre_archivo = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    fecha_subida = Column(DateTime(timezone=True), server_default=func.now())
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False, index=True)


class Medio(Base):
    __tablename__ = "medios"
    id_medio = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(160), nullable=False)
    descripcion = Column(Text, nullable=True)
    tipo = Column(String(20), nullable=False)
    url = Column(String(255), nullable=False)
    nombre_archivo = Column(String(255), nullable=False)
    fecha_publicacion = Column(DateTime(timezone=True), server_default=func.now())
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False, index=True)