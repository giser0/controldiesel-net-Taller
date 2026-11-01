
from sqlalchemy import Column, Integer, Numeric, Date, String, ForeignKey
from app.core.database import Base


class Cupo(Base):
    __tablename__ = "cupos"

    id_cupo = Column(Integer, primary_key=True, index=True)
    id_vehiculo = Column(
        Integer,
        ForeignKey("vehiculos.id_vehiculo"),
        nullable=False
    )
    cantidad_autorizada = Column(Numeric(12, 2), nullable=False)
    saldo_disponible = Column(Numeric(12, 2), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    estado = Column(String(20), nullable=False, default="PENDIENTE")
