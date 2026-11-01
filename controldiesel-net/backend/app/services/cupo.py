
from sqlalchemy import text


def crear_cupo(db, datos):
    consulta = text("""
        INSERT INTO cupos (
            id_vehiculo,
            cantidad_autorizada,
            saldo_disponible,
            fecha_inicio,
            fecha_fin,
            estado
        )
        VALUES (
            :id_vehiculo,
            :cantidad_autorizada,
            :saldo_disponible,
            :fecha_inicio,
            :fecha_fin,
            'PENDIENTE'
        )
        RETURNING
            id_cupo,
            id_vehiculo,
            cantidad_autorizada,
            saldo_disponible,
            fecha_inicio,
            fecha_fin,
            estado
    """)

    try:
        resultado = db.execute(
            consulta,
            {
                "id_vehiculo": datos.id_vehiculo,
                "cantidad_autorizada": datos.cantidad_autorizada,
                "saldo_disponible": datos.cantidad_autorizada,
                "fecha_inicio": datos.fecha_inicio,
                "fecha_fin": datos.fecha_fin,
            }
        ).mappings().one()

        db.commit()

        return dict(resultado)

    except Exception:
        db.rollback()
        raise
