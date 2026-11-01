
from sqlalchemy import Column, Integer, String
from app.core.database import Base


class Rol(Base):
    __tablename__ = "roles"

    id_rol = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(30), nullable=False, unique=True)
    descripcion = Column(String(150), nullable=True)
