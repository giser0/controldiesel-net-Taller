
from sqlalchemy import Column, Integer, String, Boolean

from app.core.database import Base


class Vehiculo(Base):
    __tablename__ = "vehiculos"

    id_vehiculo = Column(Integer, primary_key=True, index=True)
    placa = Column(String(15), nullable=False, unique=True)
    descripcion = Column(String(100), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
