
from sqlalchemy import text


def registrar_o_actualizar_alerta(
    db,
    id_vehiculo: int,
    tipo: str,
    descripcion: str,
    id_despachos: list[int]
):
    """
    Crea una alerta nueva o actualiza una alerta abierta
    del mismo vehículo y tipo.

    También relaciona los despachos involucrados.
    """

    if tipo not in ("RD-01", "RD-02"):
        raise ValueError("Tipo de alerta no válido")

    # Buscar una alerta abierta del mismo vehículo y tipo.
    alerta = db.execute(text("""
        SELECT id_alerta
        FROM alertas
        WHERE id_vehiculo = :vehiculo
          AND tipo = :tipo
          AND estado IN ('PENDIENTE', 'EN_REVISION')
        FOR UPDATE
    """), {
        "vehiculo": id_vehiculo,
        "tipo": tipo
    }).mappings().first()

    if alerta:
        # Actualizar la alerta existente.
        id_alerta = alerta["id_alerta"]

        db.execute(text("""
            UPDATE alertas
            SET
                descripcion = :descripcion,
                fecha_ultima = NOW(),
                contador = contador + 1
            WHERE id_alerta = :id_alerta
        """), {
            "descripcion": descripcion,
            "id_alerta": id_alerta
        })

    else:
        # Crear una alerta nueva.
        id_alerta = db.execute(text("""
            INSERT INTO alertas (
                id_vehiculo,
                tipo,
                estado,
                descripcion,
                fecha_creacion,
                fecha_ultima,
                contador
            )
            VALUES (
                :vehiculo,
                :tipo,
                'PENDIENTE',
                :descripcion,
                NOW(),
                NOW(),
                1
            )
            RETURNING id_alerta
        """), {
            "vehiculo": id_vehiculo,
            "tipo": tipo,
            "descripcion": descripcion
        }).scalar_one()

    # Relacionar los despachos con la alerta.
    for id_despacho in set(id_despachos):
        db.execute(text("""
            INSERT INTO alerta_despacho (
                id_alerta,
                id_despacho
            )
            VALUES (
                :alerta,
                :despacho
            )
            ON CONFLICT (id_alerta, id_despacho) DO NOTHING
        """), {
            "alerta": id_alerta,
            "despacho": id_despacho
        })

    return id_alerta
