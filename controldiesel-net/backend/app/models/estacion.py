
from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base


class Estacion(Base):
    __tablename__ = "estaciones"

    id_estacion = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    ubicacion = Column(String(200), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
