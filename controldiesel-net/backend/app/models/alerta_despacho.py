
from sqlalchemy import Column, Integer, ForeignKey
from app.core.database import Base


class AlertaDespacho(Base):
    __tablename__ = "alerta_despacho"

    id_alerta = Column(
        Integer,
        ForeignKey("alertas.id_alerta"),
        primary_key=True
    )

    id_despacho = Column(
        Integer,
        ForeignKey("despachos.id_despacho"),
        primary_key=True
    )
