
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from app.api.deps import require_roles
from app.core.database import get_db
from app.schemas.alerta import AlertaRevision, AlertaCierre
from app.services.auditoria import registrar

router = APIRouter(
    prefix="/alertas",
    tags=["alertas"]
)


@router.get("/")
def listar_alertas(
    db=Depends(get_db),
    usuario=Depends(require_roles("Regulador"))
):
    resultado = db.execute(text("""
        SELECT
            a.id_alerta,
            a.id_vehiculo,
            v.placa,
            a.tipo,
            a.estado,
            a.descripcion,
            a.fecha_creacion,
            a.fecha_ultima,
            a.contador
        FROM alertas AS a
        JOIN vehiculos AS v
            ON v.id_vehiculo = a.id_vehiculo
        ORDER BY a.fecha_ultima DESC
    """))

    return [dict(fila) for fila in resultado.mappings().all()]


@router.post("/{id_alerta}/revisar")
def revisar_alerta(
    id_alerta: int,
    datos: AlertaRevision,
    db=Depends(get_db),
    usuario=Depends(require_roles("Regulador"))
):
    try:
        alerta = db.execute(text("""
            SELECT id_alerta, estado
            FROM alertas
            WHERE id_alerta = :id_alerta
            FOR UPDATE
        """), {
            "id_alerta": id_alerta
        }).mappings().first()

        if alerta is None:
            raise HTTPException(404, "La alerta no existe")

        if alerta["estado"] != "PENDIENTE":
            raise HTTPException(
                400,
                "Solo se pueden revisar alertas pendientes"
            )

        db.execute(text("""
            UPDATE alertas
            SET estado = 'EN_REVISION',
                fecha_ultima = NOW()
            WHERE id_alerta = :id_alerta
        """), {
            "id_alerta": id_alerta
        })

        db.execute(text("""
            INSERT INTO revisiones_alerta (
                id_alerta,
                id_usuario,
                estado_anterior,
                estado_nuevo,
                observaciones,
                fecha_hora
            )
            VALUES (
                :id_alerta,
                :id_usuario,
                'PENDIENTE',
                'EN_REVISION',
                :observaciones,
                NOW()
            )
        """), {
            "id_alerta": id_alerta,
            "id_usuario": usuario["id_usuario"],
            "observaciones": datos.observaciones
        })

        registrar(
            db=db,
            accion="REVISAR_ALERTA",
            entidad="alertas",
            resultado="EXITO",
            id_usuario=usuario["id_usuario"],
            id_registro=id_alerta,
            detalle="Alerta puesta en revisión"
        )

        db.commit()

        return {
            "mensaje": "Alerta puesta en revisión correctamente",
            "id_alerta": id_alerta,
            "estado": "EN_REVISION"
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise


@router.post("/{id_alerta}/cerrar")
def cerrar_alerta(
    id_alerta: int,
    datos: AlertaCierre,
    db=Depends(get_db),
    usuario=Depends(require_roles("Regulador"))
):
    try:
        alerta = db.execute(text("""
            SELECT id_alerta, estado
            FROM alertas
            WHERE id_alerta = :id_alerta
            FOR UPDATE
        """), {
            "id_alerta": id_alerta
        }).mappings().first()

        if alerta is None:
            raise HTTPException(
                status_code=404,
                detail="La alerta no existe"
            )

        if alerta["estado"] != "EN_REVISION":
            raise HTTPException(
                status_code=400,
                detail="Solo se pueden cerrar alertas que estén en revisión"
            )

        db.execute(text("""
            UPDATE alertas
            SET estado = 'CERRADA',
                fecha_ultima = NOW()
            WHERE id_alerta = :id_alerta
        """), {
            "id_alerta": id_alerta
        })

        db.execute(text("""
            INSERT INTO revisiones_alerta (
                id_alerta,
                id_usuario,
                estado_anterior,
                estado_nuevo,
                observaciones,
                resultado,
                fecha_hora
            )
            VALUES (
                :id_alerta,
                :id_usuario,
                'EN_REVISION',
                'CERRADA',
                :observaciones,
                :resultado,
                NOW()
            )
        """), {
            "id_alerta": id_alerta,
            "id_usuario": usuario["id_usuario"],
            "observaciones": datos.observaciones,
            "resultado": datos.resultado
        })

        registrar(
            db=db,
            accion="CERRAR_ALERTA",
            entidad="alertas",
            resultado="EXITO",
            id_usuario=usuario["id_usuario"],
            id_registro=id_alerta,
            detalle=f"Alerta cerrada. Resultado: {datos.resultado}"
        )

        db.commit()

        return {
            "mensaje": "Alerta cerrada correctamente",
            "id_alerta": id_alerta,
            "estado": "CERRADA",
            "resultado": datos.resultado
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise
