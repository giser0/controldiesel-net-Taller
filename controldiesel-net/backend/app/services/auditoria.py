from sqlalchemy import text

def registrar(db, accion: str, entidad: str, resultado: str,
              id_usuario: int | None = None, id_registro: int | None = None,
              detalle: str | None = None) -> None:
    db.execute(text("""
        INSERT INTO auditoria (id_usuario, accion, entidad, id_registro, resultado, detalle)
        VALUES (:u, :a, :e, :r, :res, :d)
    """), {"u": id_usuario, "a": accion, "e": entidad, "r": id_registro,
           "res": resultado, "d": detalle})