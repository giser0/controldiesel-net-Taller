
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, text
from app.core.database import Base


class Alerta(Base):
    __tablename__ = "alertas"

    id_alerta = Column(Integer, primary_key=True, index=True)

    id_vehiculo = Column(
        Integer,
        ForeignKey("vehiculos.id_vehiculo"),
        nullable=False
    )

    tipo = Column(String(10), nullable=False)
    estado = Column(String(20), nullable=False, server_default=text("'PENDIENTE'"))
    descripcion = Column(Text, nullable=True)

    fecha_creacion = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )

    fecha_ultima = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )

    contador = Column(Integer, nullable=False, server_default=text("1"))
