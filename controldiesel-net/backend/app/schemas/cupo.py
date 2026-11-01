
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CupoCreate(BaseModel):
    id_vehiculo: int = Field(gt=0)
    cantidad_autorizada: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    fecha_inicio: date
    fecha_fin: date

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha fin no puede ser anterior a la fecha inicio")
        return self


class CupoResponse(BaseModel):
    id_cupo: int
    id_vehiculo: int
    cantidad_autorizada: Decimal
    saldo_disponible: Decimal
    fecha_inicio: date
    fecha_fin: date
    estado: str

    model_config = ConfigDict(from_attributes=True)
