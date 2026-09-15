import io
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models import Aventura, Categoria, Foto, Medio, Usuario
from app.schemas.content import AdventureCreate, CategoryCreate, ProfileUpdate


router = APIRouter(prefix="/me", tags=["Espacio personal"])
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "static" / "uploads"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
MAX_VIDEO_SIZE = 100 * 1024 * 1024


@router.get("/profile")
def get_profile(current_user: Usuario = Depends(get_current_user)):
    return {
        "id_usuario": current_user.id_usuario,
        "nombre": current_user.nombre,
        "email": current_user.email,
        "foto_perfil": current_user.foto_perfil,
        "biografia": current_user.biografia,
    }


@router.put("/profile")
def update_profile(
    profile: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    current_user.nombre = profile.nombre
    current_user.biografia = profile.biografia
    db.commit()
    db.refresh(current_user)
    return {"mensaje": "Perfil actualizado", "perfil": get_profile(current_user)}


@router.get("/categories")
def list_categories(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return db.query(Categoria).filter(Categoria.id_usuario == current_user.id_usuario).order_by(Categoria.nombre).all()


@router.post("/categories", status_code=status.HTTP_201_CREATED)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    exists = db.query(Categoria).filter(
        Categoria.id_usuario == current_user.id_usuario,
        Categoria.nombre == category.nombre,
    ).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya tienes una categoría con ese nombre")
    item = Categoria(nombre=category.nombre, id_usuario=current_user.id_usuario)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/adventures")
def list_adventures(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return db.query(Aventura).filter(Aventura.id_usuario == current_user.id_usuario).order_by(Aventura.fecha_creacion.desc()).all()


@router.post("/adventures", status_code=status.HTTP_201_CREATED)
def create_adventure(
    adventure: AdventureCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if adventure.id_categoria is not None:
        category = db.query(Categoria).filter(
            Categoria.id_categoria == adventure.id_categoria,
            Categoria.id_usuario == current_user.id_usuario,
        ).first()
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La categoría no pertenece a tu cuenta")
    item = Aventura(**adventure.model_dump(), id_usuario=current_user.id_usuario)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/photos", status_code=status.HTTP_201_CREATED)
def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Solo se permiten imágenes JPG, PNG, WEBP o GIF")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    extension = Path(file.filename or "imagen.jpg").suffix.lower() or ".jpg"
    filename = f"{current_user.id_usuario}_{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / filename
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    photo = Foto(
        nombre_archivo=file.filename or filename,
        url=f"/media/uploads/{filename}",
        id_usuario=current_user.id_usuario,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


@router.get("/photos")
def list_photos(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return db.query(Foto).filter(Foto.id_usuario == current_user.id_usuario).order_by(Foto.fecha_subida.desc()).all()


@router.get("/media")
def list_media(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return db.query(Medio).filter(Medio.id_usuario == current_user.id_usuario).order_by(Medio.fecha_publicacion.desc()).all()


@router.post("/media", status_code=status.HTTP_201_CREATED)
def upload_media(
    file: UploadFile = File(...),
    titulo: str = Form(...),
    descripcion: str = Form(default=""),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Formato no compatible")

    content = file.file.read()
    if file.content_type in ALLOWED_VIDEO_TYPES and len(content) > MAX_VIDEO_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="El video no puede superar 100 MB")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    extension = Path(file.filename or "archivo").suffix.lower() or ".bin"
    filename = f"{current_user.id_usuario}_{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / filename

    if file.content_type in ALLOWED_IMAGE_TYPES:
        try:
            image = Image.open(io.BytesIO(content))
            image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGB")
            destination = destination.with_suffix(".jpg")
            image.save(destination, "JPEG", quality=84, optimize=True)
            filename = destination.name
        except (OSError, ValueError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen no es válida")
    else:
        destination.write_bytes(content)

    media = Medio(
        titulo=titulo.strip(),
        descripcion=descripcion.strip() or None,
        tipo="imagen" if file.content_type in ALLOWED_IMAGE_TYPES else "video",
        url=f"/media/uploads/{filename}",
        nombre_archivo=file.filename or filename,
        id_usuario=current_user.id_usuario,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media