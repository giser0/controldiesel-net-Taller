
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditoriaResponse(BaseModel):
    id_auditoria: int
    id_usuario: int | None
    accion: str
    entidad: str
    id_registro: int | None
    resultado: str
    fecha_hora: datetime
    detalle: str | None

    model_config = ConfigDict(from_attributes=True)
