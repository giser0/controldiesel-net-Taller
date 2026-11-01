
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import text

from app.services.auditoria import registrar
from app.services.alerta import registrar_o_actualizar_alerta


def registrar_despacho(
    db,
    id_cupo: int,
    id_estacion: int,
    id_usuario: int,
    cantidad: Decimal,
    idempotency_key: str
):
    # 0. Comprobar si la solicitud ya fue procesada
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
        "usuario": id_usuario,
        "clave": idempotency_key
    }).mappings().first()

    if despacho_existente is not None:
        if (
            despacho_existente["id_cupo"] != id_cupo
            or despacho_existente["cantidad"] != cantidad
        ):
            raise ValueError(
                "La clave de idempotencia ya fue utilizada "
                "con otros datos"
            )

        return {
            **dict(despacho_existente),
            "reutilizado": True
        }
    # 1. Obtener la fecha actual de Bolivia
    fecha_actual = datetime.now(
        ZoneInfo("America/La_Paz")
    ).date()

    # 2. Consultar y bloquear el cupo
    cupo = db.execute(text("""
        SELECT
            id_cupo,
            id_vehiculo,
            saldo_disponible,
            fecha_inicio,
            fecha_fin,
            estado
        FROM cupos
        WHERE id_cupo = :id
        FOR UPDATE
    """), {"id": id_cupo}).mappings().first()

    if cupo is None:
        raise ValueError("El cupo no existe")

    # 3. Validar la cantidad
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero")

    # 4. Validar el estado del cupo
    if cupo["estado"] != "VIGENTE":
        raise ValueError(
            f"El cupo no está vigente. Estado actual: {cupo['estado']}"
        )

    # 5. Validar las fechas autorizadas
    if fecha_actual < cupo["fecha_inicio"]:
        raise ValueError("El cupo todavía no está vigente por fecha")

    if fecha_actual > cupo["fecha_fin"]:
        raise ValueError("El cupo ya venció por fecha")

    # 6. Validar el saldo disponible
    if cantidad > cupo["saldo_disponible"]:
        raise ValueError("Saldo insuficiente")

    # 7. Registrar el despacho
    despacho = db.execute(text("""
        INSERT INTO despachos (
            id_cupo,
            id_estacion,
            id_usuario,
            cantidad,
            idempotency_key,
            estado
        )
        VALUES (
            :cupo,
            :estacion,
            :usuario,
            :cantidad,
            :clave,
            'CONFIRMADO'
        )
        RETURNING
            id_despacho,
            id_cupo,
            id_estacion,
            id_usuario,
            cantidad,
            fecha_hora,
            estado
    """), {
        "cupo": id_cupo,
        "estacion": id_estacion,
        "usuario": id_usuario,
        "cantidad": cantidad,
        "clave": idempotency_key
    }).mappings().one()
    # 8. Descontar el saldo del cupo
    db.execute(text("""
        UPDATE cupos
        SET saldo_disponible = saldo_disponible - :cantidad
        WHERE id_cupo = :cupo
    """), {
        "cantidad": cantidad,
        "cupo": id_cupo
    })

    # 9. Obtener los despachos del mismo vehículo
    # realizados durante las últimas 12 horas.
    despachos_12h = db.execute(text("""
        SELECT
            d.id_despacho,
            d.id_estacion
        FROM despachos d
        INNER JOIN cupos c
            ON c.id_cupo = d.id_cupo
        WHERE c.id_vehiculo = :vehiculo
          AND d.estado = 'CONFIRMADO'
          AND d.fecha_hora >= NOW() - INTERVAL '12 hours'
        ORDER BY d.fecha_hora DESC
    """), {
        "vehiculo": cupo["id_vehiculo"]
    }).mappings().all()

    # 10. Regla RD-01:
    # El mismo vehículo registra despachos
    # en estaciones diferentes dentro de 12 horas.
    estaciones = {
        d["id_estacion"] for d in despachos_12h
    }

    if len(estaciones) > 1:
        ids_despachos = [
            d["id_despacho"] for d in despachos_12h
        ]

        registrar_o_actualizar_alerta(
            db=db,
            id_vehiculo=cupo["id_vehiculo"],
            tipo="RD-01",
            descripcion=("El vehículo registró despachos en estaciones diferentes dentro de 12 horas."),
            id_despachos=ids_despachos
        )

    # 11. Obtener los despachos de las últimas 24 horas.
    despachos_24h = db.execute(text("""
        SELECT
            d.id_despacho
        FROM despachos d
        INNER JOIN cupos c
            ON c.id_cupo = d.id_cupo
        WHERE c.id_vehiculo = :vehiculo
          AND d.estado = 'CONFIRMADO'
          AND d.fecha_hora >= NOW() - INTERVAL '24 hours'
        ORDER BY d.fecha_hora DESC
    """), {
        "vehiculo": cupo["id_vehiculo"]
    }).mappings().all()

    # 12. Regla RD-02:
    # Cuatro o más despachos en 24 horas.
    if len(despachos_24h) >= 4:
        ids_despachos = [
            d["id_despacho"] for d in despachos_24h
        ]

        registrar_o_actualizar_alerta(
            db=db,
            id_vehiculo=cupo["id_vehiculo"],
            tipo="RD-02",
            descripcion=(
                f"El vehículo registró {len(despachos_24h)} "
                "o más despachos dentro de 24 horas."
            ),
            id_despachos=ids_despachos
        )

    # 13. Registrar la auditoría
    registrar(
        db,
        accion="REGISTRAR_DESPACHO",
        entidad="despachos",
        resultado="EXITO",
        id_usuario=id_usuario,
        id_registro=despacho["id_despacho"],
        detalle=(
            f"Despacho de {cantidad} litros "
            f"para el cupo {id_cupo}"
        )
    )

    return {
        **dict(despacho),
        "reutilizado": False
    }
