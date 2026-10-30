from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.services import auditoria

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=1, max_length=200)

@router.post("/login")
def login(data: LoginIn, db=Depends(get_db)):
    row = db.execute(text("""
        SELECT u.id_usuario, u.password_hash, u.activo, r.nombre AS rol
        FROM usuarios u JOIN roles r USING (id_rol)
        WHERE lower(u.email) = lower(:email)
    """), {"email": data.email}).mappings().first()
    
    ok = bool(row and row["activo"] and verify_password(data.password, row["password_hash"]))
    
    if not ok:
        auditoria.registrar(db, "LOGIN_FALLIDO", "usuarios", "RECHAZADO",
                            id_usuario=row["id_usuario"] if row else None)
        db.commit()
        raise HTTPException(401, "Credenciales inválidas")
        
    auditoria.registrar(db, "LOGIN", "usuarios", "EXITO", id_usuario=row["id_usuario"])
    db.commit()
    
    return {
        "access_token": create_access_token(row["id_usuario"], row["rol"]),
        "token_type": "bearer",
        "rol": row["rol"]
    }

@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user