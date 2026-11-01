from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DespachoCreate(BaseModel):
    id_cupo: int = Field(gt=0)
    cantidad: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2
    )
    idempotency_key: str = Field(
        min_length=1,
        max_length=100
    )


class DespachoResponse(BaseModel):
    id_despacho: int
    id_cupo: int
    id_estacion: int
    id_usuario: int
    cantidad: Decimal
    fecha_hora: datetime
    estado: str

    model_config = ConfigDict(from_attributes=True)