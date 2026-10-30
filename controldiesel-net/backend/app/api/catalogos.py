from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.api.deps import require_roles
from app.core.database import get_db

router = APIRouter(tags=["catalogos"])

@router.get("/vehiculos")
def listar_vehiculos(db=Depends(get_db), _=Depends(require_roles("Administrador", "Operador"))):
    rows = db.execute(text(
        "SELECT id_vehiculo, placa, descripcion, activo FROM vehiculos ORDER BY placa"
    )).mappings().all()
    return [dict(r) for r in rows]

@router.get("/estaciones")
def listar_estaciones(db=Depends(get_db), _=Depends(require_roles("Administrador"))):
    rows = db.execute(text(
        "SELECT id_estacion, codigo, nombre, ubicacion, activo FROM estaciones ORDER BY codigo"
    )).mappings().all()
    return [dict(r) for r in rows]