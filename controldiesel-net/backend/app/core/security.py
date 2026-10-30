from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from app.core.config import settings

ALGORITHM = "HS256"

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except ValueError:
        return False

def create_access_token(id_usuario: int, rol: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(id_usuario), "rol": rol, "exp": exp},
                      settings.secret_key, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])