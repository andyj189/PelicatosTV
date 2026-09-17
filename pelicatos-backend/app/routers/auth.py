from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models import Usuario
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(Usuario).filter(Usuario.email == user_data.email).first()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese correo",
        )

    usuario = Usuario(
        nombre=user_data.nombre,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"id_usuario": usuario.id_usuario, "mensaje": "Usuario creado correctamente"}


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == credentials.email).first()

    if usuario is None or not verify_password(
        credentials.password, usuario.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )

    token = create_access_token(str(usuario.id_usuario))
    return {"access_token": token, "token_type": "bearer"}