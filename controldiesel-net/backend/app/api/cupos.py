
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.api.deps import require_roles
from app.core.database import get_db
from app.schemas.cupo import CupoCreate
from app.services.cupo import crear_cupo

router = APIRouter(prefix="/cupos", tags=["cupos"])


@router.get("/")
def listar_cupos(
    db=Depends(get_db),
    _=Depends(require_roles("Administrador"))
):
    rows = db.execute(text("""
        SELECT
            c.id_cupo,
            c.id_vehiculo,
            v.placa,
            c.cantidad_autorizada,
            c.saldo_disponible,
            c.fecha_inicio,
            c.fecha_fin,
            c.estado
        FROM cupos c
        JOIN vehiculos v ON v.id_vehiculo = c.id_vehiculo
        ORDER BY c.fecha_inicio DESC, c.id_cupo DESC
    """)).mappings().all()

    return [dict(row) for row in rows]


@router.post("/", status_code=201)
def registrar_cupo(
    datos: CupoCreate,
    db=Depends(get_db),
    _=Depends(require_roles("Administrador"))
):
    try:
        vehiculo = db.execute(text("""
            SELECT id_vehiculo
            FROM vehiculos
            WHERE id_vehiculo = :id
              AND activo = TRUE
        """), {"id": datos.id_vehiculo}).first()

        if vehiculo is None:
            raise HTTPException(
                status_code=404,
                detail="El vehículo no existe o está inactivo"
            )

        return crear_cupo(db, datos)

    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo registrar el cupo por una restricción de la base de datos"
        )
