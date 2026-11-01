
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, text
from app.core.database import Base


class RevisionAlerta(Base):
    __tablename__ = "revisiones_alerta"

    id_revision = Column(Integer, primary_key=True, index=True)

    id_alerta = Column(
        Integer,
        ForeignKey("alertas.id_alerta"),
        nullable=False
    )

    id_usuario = Column(
        Integer,
        ForeignKey("usuarios.id_usuario"),
        nullable=False
    )

    estado_anterior = Column(String(20), nullable=False)
    estado_nuevo = Column(String(20), nullable=False)
    observaciones = Column(Text, nullable=True)
    resultado = Column(String(100), nullable=True)

    fecha_hora = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
