
from pydantic import BaseModel, ConfigDict, Field


class VehiculoCreate(BaseModel):
    placa: str = Field(min_length=1, max_length=15)
    descripcion: str | None = Field(default=None, max_length=100)


class VehiculoResponse(BaseModel):
    id_vehiculo: int
    placa: str
    descripcion: str | None
    activo: bool

    model_config = ConfigDict(from_attributes=True)
