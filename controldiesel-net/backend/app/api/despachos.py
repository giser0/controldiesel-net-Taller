from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.api.deps import require_roles
from app.core.database import get_db
from app.schemas.despacho import DespachoCreate, DespachoResponse
from app.services.despacho import registrar_despacho
from app.services.auditoria import registrar


router = APIRouter(
    prefix="/despachos",
    tags=["despachos"]
)


@router.post(
    "/",
    response_model=DespachoResponse,
    status_code=201
)
def crear_despacho(
    datos: DespachoCreate,
    response: Response,
    db=Depends(get_db),
    usuario=Depends(require_roles("Operador"))
):
    # 1. Comprobar que el operador tenga una estación asignada.
    if usuario["id_estacion"] is None:
        raise HTTPException(
            status_code=403,
            detail="El operador no tiene una estación asignada"
        )

    try:
        # 2. Registrar el despacho.
        resultado = registrar_despacho(
            db=db,
            id_cupo=datos.id_cupo,
            id_estacion=usuario["id_estacion"],
            id_usuario=usuario["id_usuario"],
            cantidad=datos.cantidad,
            idempotency_key=datos.idempotency_key
        )

        # 3. Confirmar el despacho, el descuento y la auditoría.
        db.commit()

        # 4. Si ya existía el despacho, responder HTTP 200.
        if resultado.get("reutilizado"):
            response.status_code = 200

        # No enviar el campo interno "reutilizado" al cliente.
        return {
            clave: valor
            for clave, valor in resultado.items()
            if clave != "reutilizado"
        }

    except ValueError as error:
        db.rollback()

        mensaje = str(error)

        # 5. Una clave de idempotencia no puede reutilizarse
        # con datos diferentes.
        if "clave de idempotencia" in mensaje.lower():
            raise HTTPException(
                status_code=409,
                detail=mensaje
            )

        # 6. Registrar los intentos rechazados por saldo insuficiente.
        if mensaje == "Saldo insuficiente":
            try:
                registrar(
                    db,
                    accion="DESPACHO_RECHAZADO",
                    entidad="despachos",
                    resultado="RECHAZADO",
                    id_usuario=usuario["id_usuario"],
                    detalle="SALDO_INSUFICIENTE"
                )

                db.commit()

            except Exception:
                db.rollback()
                print(
                    "No se pudo guardar la auditoría "
                    "del rechazo RD-03"
                )

        raise HTTPException(
            status_code=400,
            detail=mensaje
        )

    except IntegrityError:
        # 7. Revertir la transacción si existe una restricción
        # de base de datos incumplida.
        db.rollback()

        # 8. Comprobar si otra solicitud registró el mismo despacho.
        despacho_existente = db.execute(text("""
            SELECT
                id_despacho,
                id_cupo,
                id_estacion,
                id_usuario,
                cantidad,
                fecha_hora,
                estado
            FROM despachos
            WHERE id_usuario = :usuario
              AND idempotency_key = :clave
        """), {
            "usuario": usuario["id_usuario"],
            "clave": datos.idempotency_key
        }).mappings().first()

        if despacho_existente is not None:

            # 9. Verificar que los datos de la solicitud coincidan.
            if (
                despacho_existente["id_cupo"] != datos.id_cupo
                or despacho_existente["cantidad"] != datos.cantidad
            ):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "La clave de idempotencia ya fue "
                        "utilizada con otros datos"
                    )
                )

            # 10. Si coincide, devolver el despacho existente.
            response.status_code = 200
            return dict(despacho_existente)

        # 11. Si no fue un duplicado, informar el conflicto.
        raise HTTPException(
            status_code=409,
            detail=(
                "No se pudo registrar el despacho "
                "por una restricción de la base de datos"
            )
        )