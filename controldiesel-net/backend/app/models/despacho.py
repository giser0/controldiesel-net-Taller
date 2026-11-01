
from sqlalchemy import Column, Integer, Numeric, DateTime, String, ForeignKey, text
from app.core.database import Base


class Despacho(Base):
    __tablename__ = "despachos"

    id_despacho = Column(Integer, primary_key=True, index=True)

    id_cupo = Column(
        Integer,
        ForeignKey("cupos.id_cupo"),
        nullable=False
    )

    id_estacion = Column(
        Integer,
        ForeignKey("estaciones.id_estacion"),
        nullable=False
    )

    id_usuario = Column(
        Integer,
        ForeignKey("usuarios.id_usuario"),
        nullable=False
    )

    cantidad = Column(Numeric(12, 2), nullable=False)

    fecha_hora = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )

    estado = Column(
        String(20),
        nullable=False,
        server_default=text("'CONFIRMADO'")
    )
