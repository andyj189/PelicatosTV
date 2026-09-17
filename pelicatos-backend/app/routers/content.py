import io
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models import Aventura, Categoria, Foto, Medio, Perfil, Usuario
from app.schemas.content import AdventureCreate, AdventureUpdate, CategoryCreate, ProfileUpdate, SiteSettingsUpdate


router = APIRouter(prefix="/me", tags=["Espacio personal"])
public_router = APIRouter(prefix="/public", tags=["Sitios públicos"])
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


def get_or_create_site(db: Session, current_user: Usuario):
    site = db.query(Perfil).filter(Perfil.id_usuario == current_user.id_usuario).first()
    if site is None:
        site = Perfil(id_usuario=current_user.id_usuario, nombre_mostrar=current_user.nombre)
        db.add(site)
        db.commit()
        db.refresh(site)
    return site


@router.get("/site")
def get_site(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    site = get_or_create_site(db, current_user)
    return {
        "nombre_mostrar": site.nombre_mostrar or current_user.nombre,
        "descripcion": site.descripcion,
        "logo": site.logo,
        "fondo_url": site.fondo_url,
        "hero_image_url": site.hero_image_url,
        "hero_eyebrow": site.hero_eyebrow,
        "hero_titulo": site.hero_titulo,
        "hero_descripcion": site.hero_descripcion,
        "facebook_url": site.facebook_url,
        "instagram_url": site.instagram_url,
        "tiktok_url": site.tiktok_url,
        "youtube_url": site.youtube_url,
        "footer_descripcion": site.footer_descripcion,
        "copyright_texto": site.copyright_texto,
        "id_usuario": current_user.id_usuario,
    }


@router.put("/site")
def update_site(
    settings: SiteSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    site = get_or_create_site(db, current_user)
    for field, value in settings.model_dump().items():
        setattr(site, field, value)
    db.commit()
    db.refresh(site)
    return get_site(db, current_user)


def upload_site_image(file: UploadFile, field_name: str, db: Session, current_user: Usuario):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Solo se permiten imágenes JPG, PNG, WEBP o GIF")
    content = file.file.read()
    try:
        image = Image.open(io.BytesIO(content))
        image.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
    except (OSError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen no es válida")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{current_user.id_usuario}_{field_name}_{uuid4().hex}.jpg"
    destination = UPLOAD_DIR / filename
    image.save(destination, "JPEG", quality=86, optimize=True)
    site = get_or_create_site(db, current_user)
    setattr(site, field_name, f"/media/uploads/{filename}")
    db.commit()
    db.refresh(site)
    return get_site(db, current_user)


@router.post("/site/logo")
def upload_site_logo(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return upload_site_image(file, "logo", db, current_user)


@router.post("/site/background")
def upload_site_background(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return upload_site_image(file, "fondo_url", db, current_user)


@router.post("/site/hero-image")
def upload_site_hero_image(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return upload_site_image(file, "hero_image_url", db, current_user)


@public_router.get("/site/{user_id}")
def get_public_site(user_id: int, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El sitio no existe")
    site = db.query(Perfil).filter(Perfil.id_usuario == user_id).first()
    adventures = db.query(Aventura).filter(Aventura.id_usuario == user_id).order_by(Aventura.fecha_creacion.desc()).all()
    media = db.query(Medio).filter(Medio.id_usuario == user_id).order_by(Medio.fecha_publicacion.desc()).all()
    photos = db.query(Foto).filter(Foto.id_usuario == user_id).order_by(Foto.fecha_subida.desc()).all()
    return {
        "nombre_mostrar": (site.nombre_mostrar if site else None) or user.nombre,
        "descripcion": site.descripcion if site else None,
        "logo": site.logo if site else None,
        "fondo_url": site.fondo_url if site else None,
        "hero_image_url": site.hero_image_url if site else None,
        "hero_eyebrow": site.hero_eyebrow if site else None,
        "hero_titulo": site.hero_titulo if site else None,
        "hero_descripcion": site.hero_descripcion if site else None,
        "facebook_url": site.facebook_url if site else None,
        "instagram_url": site.instagram_url if site else None,
        "tiktok_url": site.tiktok_url if site else None,
        "youtube_url": site.youtube_url if site else None,
        "footer_descripcion": site.footer_descripcion if site else None,
        "copyright_texto": site.copyright_texto if site else None,
        "aventuras": [
            {
                "id_aventura": item.id_aventura,
                "titulo": item.titulo,
                "contenido": item.contenido,
                "ubicacion": item.ubicacion,
                "imagen_url": item.imagen_url,
            }
            for item in adventures
        ],
        "media": [
            {
                "id_medio": item.id_medio,
                "titulo": item.titulo,
                "descripcion": item.descripcion,
                "tipo": item.tipo,
                "url": item.url,
            }
            for item in media
        ],
        "fotos": [
            {
                "id_foto": item.id_foto,
                "nombre_archivo": item.nombre_archivo,
                "url": item.url,
            }
            for item in photos
        ],
    }


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


@router.put("/adventures/{adventure_id}")
def update_adventure(
    adventure_id: int,
    adventure: AdventureUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    item = db.query(Aventura).filter(
        Aventura.id_aventura == adventure_id,
        Aventura.id_usuario == current_user.id_usuario,
    ).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La aventura no existe")
    if adventure.id_categoria is not None:
        category = db.query(Categoria).filter(
            Categoria.id_categoria == adventure.id_categoria,
            Categoria.id_usuario == current_user.id_usuario,
        ).first()
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La categoría no pertenece a tu cuenta")
    for field, value in adventure.model_dump().items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.post("/adventures/{adventure_id}/image", status_code=status.HTTP_201_CREATED)
def upload_adventure_image(
    adventure_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Solo se permiten imágenes JPG, PNG, WEBP o GIF")
    item = db.query(Aventura).filter(
        Aventura.id_aventura == adventure_id,
        Aventura.id_usuario == current_user.id_usuario,
    ).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La aventura no existe")
    content = file.file.read()
    try:
        image = Image.open(io.BytesIO(content))
        image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
    except (OSError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La imagen no es válida")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{current_user.id_usuario}_{uuid4().hex}.jpg"
    destination = UPLOAD_DIR / filename
    image.save(destination, "JPEG", quality=84, optimize=True)
    item.imagen_url = f"/media/uploads/{filename}"
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