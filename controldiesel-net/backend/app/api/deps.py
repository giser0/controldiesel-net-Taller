import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from app.core.database import get_db
from app.core.security import decode_token

bearer = HTTPBearer(auto_error=False)

def get_current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer),
                     db=Depends(get_db)) -> dict:
    if cred is None:
        raise HTTPException(401, "No autenticado", headers={"WWW-Authenticate": "Bearer"})
    try:
        uid = int(decode_token(cred.credentials)["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Token inválido o vencido", headers={"WWW-Authenticate": "Bearer"})
    
    # Consulta la base en cada petición para verificar si sigue activo y su rol actual
    row = db.execute(text("""
        SELECT u.id_usuario, u.nombre, u.email, u.id_estacion, r.nombre AS rol
        FROM usuarios u JOIN roles r USING (id_rol)
        WHERE u.id_usuario = :id AND u.activo
    """), {"id": uid}).mappings().first()
    
    if row is None:
        raise HTTPException(401, "Usuario no válido", headers={"WWW-Authenticate": "Bearer"})
    return dict(row)

def require_roles(*roles: str):
    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["rol"] not in roles:
            raise HTTPException(403, "No tiene permiso para esta operación")
        return user
    return checker