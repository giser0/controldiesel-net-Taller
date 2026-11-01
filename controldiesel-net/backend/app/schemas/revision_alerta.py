
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class RevisionAlertaCreate(BaseModel):
    estado_nuevo: Literal["EN_REVISION", "CERRADA"]
    observaciones: str | None = None
    resultado: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validar_cierre(self):
        if self.estado_nuevo == "CERRADA" and not self.resultado:
            raise ValueError("Debe indicar un resultado para cerrar la alerta")
        return self
