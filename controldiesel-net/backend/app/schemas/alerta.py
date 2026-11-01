
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlertaResponse(BaseModel):
    id_alerta: int
    id_vehiculo: int
    tipo: str
    estado: str
    descripcion: str | None
    fecha_creacion: datetime
    fecha_ultima: datetime
    contador: int

    model_config = ConfigDict(from_attributes=True)


class AlertaRevision(BaseModel):
    observaciones: str = Field(
        min_length=5,
        max_length=1000
    )

class AlertaCierre(BaseModel):
    observaciones: str = Field(
        min_length=5,
        max_length=1000
    )

    resultado: str = Field(
        pattern="^(JUSTIFICADA|REQUIERE_SEGUIMIENTO)$"
    )

