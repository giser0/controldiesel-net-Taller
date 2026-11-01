
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.core.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)

    id_rol = Column(Integer, ForeignKey("roles.id_rol"), nullable=False)

    id_estacion = Column(
        Integer,
        ForeignKey("estaciones.id_estacion"),
        nullable=True
    )

    nombre = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
