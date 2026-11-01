
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, text
from app.core.database import Base


class Auditoria(Base):
    __tablename__ = "auditoria"

    id_auditoria = Column(Integer, primary_key=True, index=True)

    id_usuario = Column(
        Integer,
        ForeignKey("usuarios.id_usuario"),
        nullable=True
    )

    accion = Column(String(100), nullable=False)
    entidad = Column(String(50), nullable=False)
    id_registro = Column(Integer, nullable=True)
    resultado = Column(String(40), nullable=False)

    fecha_hora = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )

    detalle = Column(Text, nullable=True)
