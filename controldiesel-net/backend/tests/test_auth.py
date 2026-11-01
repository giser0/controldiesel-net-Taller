from fastapi.testclient import TestClient
from app.main import app
from sqlalchemy import text

client = TestClient(app)

def login(email, password):
    return client.post("/auth/login", json={"email": email, "password": password})

def auth(token):
    return {"Authorization": f"Bearer {token}"}

def test_health():
    assert client.get("/health").status_code == 200

def test_login_correcto():
    r = login("admin@controldiesel.test", "Admin#2026")
    assert r.status_code == 200 and r.json()["rol"] == "Administrador"

def test_login_clave_incorrecta():
    assert login("admin@controldiesel.test", "mala").status_code == 401

def test_login_usuario_inexistente():
    assert login("nadie@controldiesel.test", "x").status_code == 401

def test_ruta_protegida_sin_token():
    assert client.get("/vehiculos").status_code == 401

def test_operador_no_puede_ver_estaciones():
    token = login("operador1@controldiesel.test", "Operador1#2026").json()["access_token"]
    assert client.get("/estaciones", headers=auth(token)).status_code == 403

def test_admin_ve_estaciones():
    token = login("admin@controldiesel.test", "Admin#2026").json()["access_token"]
    r = client.get("/estaciones", headers=auth(token))
    assert r.status_code == 200 and len(r.json()) >= 3
def test_operador_no_puede_ver_cupos():
    token = login(
        "operador1@controldiesel.test",
        "Operador1#2026"
    ).json()["access_token"]

    r = client.get("/cupos/", headers=auth(token))

    assert r.status_code == 403


def test_admin_puede_ver_cupos():
    token = login(
        "admin@controldiesel.test",
        "Admin#2026"
    ).json()["access_token"]

    r = client.get("/cupos/", headers=auth(token))

    assert r.status_code == 200

def test_operador_no_puede_crear_cupos():
    token = login(
        "operador1@controldiesel.test",
        "Operador1#2026"
    ).json()["access_token"]

    datos = {
        "id_vehiculo": 4,
        "cantidad_autorizada": 100,
        "fecha_inicio": "2026-11-01",
        "fecha_fin": "2026-11-30"
    }

    r = client.post(
        "/cupos/",
        json=datos,
        headers=auth(token)
    )

    assert r.status_code == 403
def test_admin_puede_crear_cupo(test_db_session):
    from datetime import date, timedelta
    from uuid import uuid4
    from sqlalchemy import text

    # Crear un vehículo exclusivo para esta prueba
    placa = f"TST-{uuid4().hex[:8].upper()}"

    resultado = test_db_session.execute(
        text("""
            INSERT INTO vehiculos (placa)
            VALUES (:placa)
            RETURNING id_vehiculo
        """),
        {"placa": placa}
    ).mappings().one()

    id_vehiculo = resultado["id_vehiculo"]
    test_db_session.commit()

    try:
        token = login(
            "admin@controldiesel.test",
            "Admin#2026"
        ).json()["access_token"]

        fecha_inicio = date.today()
        fecha_fin = fecha_inicio + timedelta(days=30)

        datos = {
            "id_vehiculo": id_vehiculo,
            "cantidad_autorizada": 100,
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_fin": fecha_fin.isoformat()
        }

        r = client.post(
            "/cupos/",
            json=datos,
            headers=auth(token)
        )

        assert r.status_code == 201, r.text

        respuesta = r.json()

        assert respuesta["id_vehiculo"] == id_vehiculo
        assert float(respuesta["cantidad_autorizada"]) == 100
        assert float(respuesta["saldo_disponible"]) == 100
        assert respuesta["estado"] == "PENDIENTE"

    finally:
        # Limpiar únicamente los datos creados para esta prueba
        test_db_session.execute(
            text("DELETE FROM cupos WHERE id_vehiculo = :id"),
            {"id": id_vehiculo}
        )
        test_db_session.execute(
            text("DELETE FROM vehiculos WHERE id_vehiculo = :id"),
            {"id": id_vehiculo}
        )
        test_db_session.commit()
def test_operador_puede_registrar_despacho(test_db_session):
    from datetime import date, timedelta
    from uuid import uuid4
    from sqlalchemy import text

    # Crear un vehículo exclusivo para esta prueba
    placa = f"DSP-{uuid4().hex[:8].upper()}"

    vehiculo = test_db_session.execute(
        text("""
            INSERT INTO vehiculos (placa, descripcion)
            VALUES (:placa, 'Vehículo temporal para prueba de despacho')
            RETURNING id_vehiculo
        """),
        {"placa": placa}
    ).mappings().one()

    id_vehiculo = vehiculo["id_vehiculo"]

    # Crear un cupo vigente con 100 litros
    cupo = test_db_session.execute(
        text("""
            INSERT INTO cupos (
                id_vehiculo,
                cantidad_autorizada,
                saldo_disponible,
                fecha_inicio,
                fecha_fin,
                estado
            )
            VALUES (
                :vehiculo,
                100,
                100,
                :inicio,
                :fin,
                'VIGENTE'
            )
            RETURNING id_cupo
        """),
        {
            "vehiculo": id_vehiculo,
            "inicio": date.today(),
            "fin": date.today() + timedelta(days=30)
        }
    ).mappings().one()

    id_cupo = cupo["id_cupo"]
    test_db_session.commit()

    id_despacho = None

    try:
        token = login(
            "operador1@controldiesel.test",
            "Operador1#2026"
        ).json()["access_token"]

        r = client.post(
            "/despachos/",
        json={
            "id_cupo": id_cupo,
            "cantidad": 20,
            "idempotency_key": str(uuid4())
        },
            headers=auth(token)
        )

        assert r.status_code == 201, r.text

        respuesta = r.json()
        id_despacho = respuesta["id_despacho"]

        assert respuesta["id_cupo"] == id_cupo
        assert float(respuesta["cantidad"]) == 20
        assert respuesta["estado"] == "CONFIRMADO"

        # Comprobar que el saldo disminuyó de 100 a 80
        saldo = test_db_session.execute(
            text("""
                SELECT saldo_disponible
                FROM cupos
                WHERE id_cupo = :id
            """),
            {"id": id_cupo}
        ).scalar_one()

        assert float(saldo) == 80

    finally:
        if id_despacho is not None:
            test_db_session.execute(
                text("""
                    DELETE FROM auditoria
                    WHERE entidad = 'despachos'
                      AND id_registro = :id
                """),
                {"id": id_despacho}
            )

            test_db_session.execute(
                text("""
                    DELETE FROM despachos
                    WHERE id_despacho = :id
                """),
                {"id": id_despacho}
            )

        test_db_session.execute(
            text("DELETE FROM cupos WHERE id_cupo = :id"),
            {"id": id_cupo}
        )

        test_db_session.execute(
            text("DELETE FROM vehiculos WHERE id_vehiculo = :id"),
            {"id": id_vehiculo}
        )

        test_db_session.commit()
def test_alerta_rd01_despachos_en_estaciones_diferentes(test_db_session):
    from datetime import date, timedelta
    from uuid import uuid4
    from sqlalchemy import text

    placa = f"RD01-{uuid4().hex[:8].upper()}"

    vehiculo = test_db_session.execute(text("""
        INSERT INTO vehiculos (placa, descripcion)
        VALUES (:placa, 'Vehículo temporal para prueba RD-01')
        RETURNING id_vehiculo
    """), {"placa": placa}).mappings().one()

    id_vehiculo = vehiculo["id_vehiculo"]

    cupo = test_db_session.execute(text("""
        INSERT INTO cupos (
            id_vehiculo, cantidad_autorizada, saldo_disponible,
            fecha_inicio, fecha_fin, estado
        )
        VALUES (:vehiculo, 100, 100, :inicio, :fin, 'VIGENTE')
        RETURNING id_cupo
    """), {
        "vehiculo": id_vehiculo,
        "inicio": date.today(),
        "fin": date.today() + timedelta(days=30)
    }).mappings().one()

    id_cupo = cupo["id_cupo"]
    test_db_session.commit()

    id_despachos = []

    try:
        operadores = [
            ("operador1@controldiesel.test", "Operador1#2026"),
            ("operador2@controldiesel.test", "Operador2#2026"),
        ]

        for email, password in operadores:
            token = login(email, password).json()["access_token"]

            respuesta = client.post(
                "/despachos/",
                json={"id_cupo": id_cupo, "cantidad": 10, "idempotency_key": str(uuid4())},
                headers=auth(token)
            )

            assert respuesta.status_code == 201, respuesta.text
            id_despachos.append(respuesta.json()["id_despacho"])

        alerta = test_db_session.execute(text("""
            SELECT id_alerta, tipo, estado, contador
            FROM alertas
            WHERE id_vehiculo = :vehiculo
              AND tipo = 'RD-01'
        """), {"vehiculo": id_vehiculo}).mappings().one_or_none()

        assert alerta is not None
        assert alerta["estado"] == "PENDIENTE"
        assert alerta["contador"] == 1

        relaciones = test_db_session.execute(text("""
            SELECT COUNT(*)
            FROM alerta_despacho
            WHERE id_alerta = :alerta
        """), {"alerta": alerta["id_alerta"]}).scalar_one()

        assert relaciones == 2

    finally:
        test_db_session.execute(text("""
            DELETE FROM alerta_despacho
            WHERE id_alerta IN (
                SELECT id_alerta FROM alertas
                WHERE id_vehiculo = :vehiculo
            )
        """), {"vehiculo": id_vehiculo})

        test_db_session.execute(text("""
            DELETE FROM alertas WHERE id_vehiculo = :vehiculo
        """), {"vehiculo": id_vehiculo})

        for id_despacho in id_despachos:
            test_db_session.execute(text("""
                DELETE FROM auditoria
                WHERE entidad = 'despachos' AND id_registro = :despacho
            """), {"despacho": id_despacho})

        test_db_session.execute(text("""
            DELETE FROM despachos WHERE id_cupo = :cupo
        """), {"cupo": id_cupo})

        test_db_session.execute(text("""
            DELETE FROM cupos WHERE id_cupo = :cupo
        """), {"cupo": id_cupo})

        test_db_session.execute(text("""
            DELETE FROM vehiculos WHERE id_vehiculo = :vehiculo
        """), {"vehiculo": id_vehiculo})

        test_db_session.commit()
def test_alerta_rd02_cuatro_despachos_en_24_horas(test_db_session):
    from datetime import date, timedelta
    from uuid import uuid4
    from sqlalchemy import text

    placa = f"RD02-{uuid4().hex[:8].upper()}"

    vehiculo = test_db_session.execute(text("""
        INSERT INTO vehiculos (placa, descripcion)
        VALUES (:placa, 'Vehículo temporal para prueba RD-02')
        RETURNING id_vehiculo
    """), {"placa": placa}).mappings().one()

    id_vehiculo = vehiculo["id_vehiculo"]

    cupo = test_db_session.execute(text("""
        INSERT INTO cupos (
            id_vehiculo, cantidad_autorizada, saldo_disponible,
            fecha_inicio, fecha_fin, estado
        )
        VALUES (:vehiculo, 100, 100, :inicio, :fin, 'VIGENTE')
        RETURNING id_cupo
    """), {
        "vehiculo": id_vehiculo,
        "inicio": date.today(),
        "fin": date.today() + timedelta(days=30)
    }).mappings().one()

    id_cupo = cupo["id_cupo"]
    test_db_session.commit()

    id_despachos = []

    try:
        token = login(
            "operador1@controldiesel.test",
            "Operador1#2026"
        ).json()["access_token"]

        for _ in range(4):
            respuesta = client.post(
                "/despachos/",
                json={"id_cupo": id_cupo, "cantidad": 5, "idempotency_key": str(uuid4())},
                headers=auth(token)
            )

            assert respuesta.status_code == 201, respuesta.text
            id_despachos.append(respuesta.json()["id_despacho"])

        alerta = test_db_session.execute(text("""
            SELECT id_alerta, tipo, estado, contador
            FROM alertas
            WHERE id_vehiculo = :vehiculo
              AND tipo = 'RD-02'
        """), {"vehiculo": id_vehiculo}).mappings().one_or_none()

        assert alerta is not None
        assert alerta["estado"] == "PENDIENTE"
        assert alerta["contador"] == 1

        relaciones = test_db_session.execute(text("""
            SELECT COUNT(*)
            FROM alerta_despacho
            WHERE id_alerta = :alerta
        """), {"alerta": alerta["id_alerta"]}).scalar_one()

        assert relaciones == 4

    finally:
        test_db_session.execute(text("""
            DELETE FROM alerta_despacho
            WHERE id_alerta IN (
                SELECT id_alerta FROM alertas
                WHERE id_vehiculo = :vehiculo
            )
        """), {"vehiculo": id_vehiculo})

        test_db_session.execute(text("""
            DELETE FROM alertas WHERE id_vehiculo = :vehiculo
        """), {"vehiculo": id_vehiculo})

        for id_despacho in id_despachos:
            test_db_session.execute(text("""
                DELETE FROM auditoria
                WHERE entidad = 'despachos' AND id_registro = :despacho
            """), {"despacho": id_despacho})

        test_db_session.execute(text("""
            DELETE FROM despachos WHERE id_cupo = :cupo
        """), {"cupo": id_cupo})

        test_db_session.execute(text("""
            DELETE FROM cupos WHERE id_cupo = :cupo
        """), {"cupo": id_cupo})

        test_db_session.execute(text("""
            DELETE FROM vehiculos WHERE id_vehiculo = :vehiculo
        """), {"vehiculo": id_vehiculo})

        test_db_session.commit()
def test_actualizar_alerta_existente_sin_duplicarla(test_db_session):
    from datetime import date, timedelta
    from uuid import uuid4
    from sqlalchemy import text

    placa = f"ACT-{uuid4().hex[:8].upper()}"

    vehiculo = test_db_session.execute(text("""
        INSERT INTO vehiculos (placa, descripcion)
        VALUES (:placa, 'Vehículo temporal para prueba de actualización')
        RETURNING id_vehiculo
    """), {"placa": placa}).mappings().one()

    id_vehiculo = vehiculo["id_vehiculo"]

    cupo = test_db_session.execute(text("""
        INSERT INTO cupos (
            id_vehiculo, cantidad_autorizada, saldo_disponible,
            fecha_inicio, fecha_fin, estado
        )
        VALUES (:vehiculo, 100, 100, :inicio, :fin, 'VIGENTE')
        RETURNING id_cupo
    """), {
        "vehiculo": id_vehiculo,
        "inicio": date.today(),
        "fin": date.today() + timedelta(days=30)
    }).mappings().one()

    id_cupo = cupo["id_cupo"]
    test_db_session.commit()

    id_despachos = []

    try:
        token = login(
            "operador1@controldiesel.test",
            "Operador1#2026"
        ).json()["access_token"]

        for _ in range(5):
            respuesta = client.post(
                "/despachos/",
                json={"id_cupo": id_cupo, "cantidad": 5, "idempotency_key": str(uuid4())},
                headers=auth(token)
            )

            assert respuesta.status_code == 201, respuesta.text
            id_despachos.append(respuesta.json()["id_despacho"])

        alertas = test_db_session.execute(text("""
            SELECT id_alerta, contador, estado
            FROM alertas
            WHERE id_vehiculo = :vehiculo
              AND tipo = 'RD-02'
        """), {"vehiculo": id_vehiculo}).mappings().all()

        assert len(alertas) == 1
        assert alertas[0]["contador"] == 2
        assert alertas[0]["estado"] == "PENDIENTE"

        relaciones = test_db_session.execute(text("""
            SELECT COUNT(*)
            FROM alerta_despacho
            WHERE id_alerta = :alerta
        """), {"alerta": alertas[0]["id_alerta"]}).scalar_one()

        assert relaciones == 5

    finally:
        test_db_session.execute(text("""
            DELETE FROM alerta_despacho
            WHERE id_alerta IN (
                SELECT id_alerta FROM alertas
                WHERE id_vehiculo = :vehiculo
            )
        """), {"vehiculo": id_vehiculo})

        test_db_session.execute(text("""
            DELETE FROM alertas WHERE id_vehiculo = :vehiculo
        """), {"vehiculo": id_vehiculo})

        for id_despacho in id_despachos:
            test_db_session.execute(text("""
                DELETE FROM auditoria
                WHERE entidad = 'despachos' AND id_registro = :despacho
            """), {"despacho": id_despacho})

        test_db_session.execute(text("""
            DELETE FROM despachos WHERE id_cupo = :cupo
        """), {"cupo": id_cupo})

        test_db_session.execute(text("""
            DELETE FROM cupos WHERE id_cupo = :cupo
        """), {"cupo": id_cupo})

        test_db_session.execute(text("""
            DELETE FROM vehiculos WHERE id_vehiculo = :vehiculo
        """), {"vehiculo": id_vehiculo})

        test_db_session.commit()
def test_rd03_rechaza_saldo_insuficiente_y_registra_auditoria(test_db_session):
    from datetime import date, timedelta
    from uuid import uuid4
    from sqlalchemy import text

    placa = f"RD03-{uuid4().hex[:8].upper()}"

    vehiculo = test_db_session.execute(text("""
        INSERT INTO vehiculos (placa, descripcion)
        VALUES (:placa, 'Vehículo temporal para prueba RD-03')
        RETURNING id_vehiculo
    """), {"placa": placa}).mappings().one()

    id_vehiculo = vehiculo["id_vehiculo"]

    cupo = test_db_session.execute(text("""
        INSERT INTO cupos (
            id_vehiculo,
            cantidad_autorizada,
            saldo_disponible,
            fecha_inicio,
            fecha_fin,
            estado
        )
        VALUES (
            :vehiculo, 100, 100, :inicio, :fin, 'VIGENTE'
        )
        RETURNING id_cupo
    """), {
        "vehiculo": id_vehiculo,
        "inicio": date.today(),
        "fin": date.today() + timedelta(days=30)
    }).mappings().one()

    id_cupo = cupo["id_cupo"]
    test_db_session.commit()

    try:
        # Contar auditorías RD-03 antes del intento
        auditorias_antes = test_db_session.execute(text("""
            SELECT COUNT(*)
            FROM auditoria
            WHERE accion = 'DESPACHO_RECHAZADO'
              AND entidad = 'despachos'
              AND detalle = 'SALDO_INSUFICIENTE'
        """)).scalar_one()

        token = login(
            "operador1@controldiesel.test",
            "Operador1#2026"
        ).json()["access_token"]

        # Intentar despachar 120 litros teniendo solo 100
        respuesta = client.post(
            "/despachos/",
            json={
                "id_cupo": id_cupo,
                "cantidad": 120,
                "idempotency_key": str(uuid4())
            },
            headers=auth(token)
        )

        assert respuesta.status_code == 400, respuesta.text
        assert respuesta.json()["detail"] == "Saldo insuficiente"

        # Comprobar que el saldo sigue en 100 litros
        saldo = test_db_session.execute(text("""
            SELECT saldo_disponible
            FROM cupos
            WHERE id_cupo = :id
        """), {"id": id_cupo}).scalar_one()

        assert float(saldo) == 100

        # Comprobar que no se creó un despacho confirmado
        despachos = test_db_session.execute(text("""
            SELECT COUNT(*)
            FROM despachos
            WHERE id_cupo = :id
        """), {"id": id_cupo}).scalar_one()

        assert despachos == 0

        # Comprobar que se registró la auditoría del rechazo
        auditorias_despues = test_db_session.execute(text("""
            SELECT COUNT(*)
            FROM auditoria
            WHERE accion = 'DESPACHO_RECHAZADO'
              AND entidad = 'despachos'
              AND detalle = 'SALDO_INSUFICIENTE'
        """)).scalar_one()

        assert auditorias_despues == auditorias_antes + 1

        # Comprobar que no se creó una alerta RD-03
        alertas = test_db_session.execute(text("""
            SELECT COUNT(*)
            FROM alertas
            WHERE id_vehiculo = :vehiculo
              AND tipo = 'RD-03'
        """), {"vehiculo": id_vehiculo}).scalar_one()

        assert alertas == 0

    finally:
        # Limpiar únicamente el cupo y vehículo temporales.
        # La auditoría del rechazo se conserva como evidencia.
        test_db_session.execute(text("""
            DELETE FROM cupos WHERE id_cupo = :id
        """), {"id": id_cupo})

        test_db_session.execute(text("""
            DELETE FROM vehiculos WHERE id_vehiculo = :id
        """), {"id": id_vehiculo})

        test_db_session.commit()
def test_p18_revierte_despacho_si_falla_auditoria(test_db_session, monkeypatch):
    from datetime import date, timedelta
    from uuid import uuid4
    from sqlalchemy import text
    import app.services.despacho as servicio_despacho

    placa = f"P18-{uuid4().hex[:8].upper()}"

    vehiculo = test_db_session.execute(text("""
        INSERT INTO vehiculos (placa, descripcion)
        VALUES (:placa, 'Vehículo temporal para prueba P18')
        RETURNING id_vehiculo
    """), {"placa": placa}).mappings().one()

    id_vehiculo = vehiculo["id_vehiculo"]

    cupo = test_db_session.execute(text("""
        INSERT INTO cupos (
            id_vehiculo, cantidad_autorizada, saldo_disponible,
            fecha_inicio, fecha_fin, estado
        )
        VALUES (:vehiculo, 100, 100, :inicio, :fin, 'VIGENTE')
        RETURNING id_cupo
    """), {
        "vehiculo": id_vehiculo,
        "inicio": date.today(),
        "fin": date.today() + timedelta(days=30)
    }).mappings().one()

    id_cupo = cupo["id_cupo"]
    test_db_session.commit()

    # Simular un fallo al guardar la auditoría
    def fallo_auditoria(*args, **kwargs):
        raise RuntimeError("Fallo simulado al guardar auditoría")

    monkeypatch.setattr(
        servicio_despacho,
        "registrar",
        fallo_auditoria
    )

    try:
        token = login(
            "operador1@controldiesel.test",
            "Operador1#2026"
        ).json()["access_token"]

        # La petición debe fallar y propagar el error simulado
        import pytest

        with pytest.raises(
            RuntimeError,
            match="Fallo simulado al guardar auditoría"
        ):
            client.post(
                "/despachos/",
                json={"id_cupo": id_cupo, "cantidad": 20, "idempotency_key": str(uuid4())},
                headers=auth(token)
            )

        # El saldo debe permanecer intacto
        saldo = test_db_session.execute(text("""
            SELECT saldo_disponible
            FROM cupos
            WHERE id_cupo = :id
        """), {"id": id_cupo}).scalar_one()

        assert float(saldo) == 100

        # No debe quedar ningún despacho confirmado
        cantidad_despachos = test_db_session.execute(text("""
            SELECT COUNT(*)
            FROM despachos
            WHERE id_cupo = :id
        """), {"id": id_cupo}).scalar_one()

        assert cantidad_despachos == 0

    finally:
        test_db_session.execute(text("""
            DELETE FROM cupos WHERE id_cupo = :id
        """), {"id": id_cupo})

        test_db_session.execute(text("""
            DELETE FROM vehiculos WHERE id_vehiculo = :id
        """), {"id": id_vehiculo})

        test_db_session.commit()
def test_p09_dos_despachos_simultaneos_no_generan_sobregiro(test_db_session):
    from datetime import date, timedelta
    from uuid import uuid4
    from concurrent.futures import ThreadPoolExecutor
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    placa = f"P09-{uuid4().hex[:8].upper()}"

    vehiculo = test_db_session.execute(text("""
        INSERT INTO vehiculos (placa, descripcion)
        VALUES (:placa, 'Vehiculo temporal para prueba P09')
        RETURNING id_vehiculo
    """), {"placa": placa}).mappings().one()

    id_vehiculo = vehiculo["id_vehiculo"]

    cupo = test_db_session.execute(text("""
        INSERT INTO cupos (
            id_vehiculo,
            cantidad_autorizada,
            saldo_disponible,
            fecha_inicio,
            fecha_fin,
            estado
        )
        VALUES (
            :vehiculo, 100, 100, :inicio, :fin, 'VIGENTE'
        )
        RETURNING id_cupo
    """), {
        "vehiculo": id_vehiculo,
        "inicio": date.today(),
        "fin": date.today() + timedelta(days=30)
    }).mappings().one()

    id_cupo = cupo["id_cupo"]
    test_db_session.commit()

    id_despachos = []

    try:
        operadores = [
            ("operador1@controldiesel.test", "Operador1#2026"),
            ("operador2@controldiesel.test", "Operador2#2026"),
        ]

        tokens = []

        for email, password in operadores:
            respuesta = login(email, password)
            assert respuesta.status_code == 200, respuesta.text
            tokens.append(respuesta.json()["access_token"])

        def solicitar_despacho(token):
            with TestClient(app) as cliente:
                return cliente.post(
                    "/despachos/",
                    json={
                        "id_cupo": id_cupo,
                        "cantidad": 70,
                        "idempotency_key": str(uuid4())
                    },
                    headers=auth(token)
                )

        with ThreadPoolExecutor(max_workers=2) as executor:
            futuros = [
                executor.submit(solicitar_despacho, token)
                for token in tokens
            ]

            respuestas = [
                futuro.result()
                for futuro in futuros
            ]

        estados = sorted(r.status_code for r in respuestas)

        assert estados == [201, 400], [
            (r.status_code, r.text) for r in respuestas
        ]

        for respuesta in respuestas:
            if respuesta.status_code == 201:
                id_despachos.append(
                    respuesta.json()["id_despacho"]
                )

        test_db_session.expire_all()

        saldo = test_db_session.execute(text("""
            SELECT saldo_disponible
            FROM cupos
            WHERE id_cupo = :id
        """), {"id": id_cupo}).scalar_one()

        cantidad_despachos = test_db_session.execute(text("""
            SELECT COUNT(*)
            FROM despachos
            WHERE id_cupo = :id
              AND estado = 'CONFIRMADO'
        """), {"id": id_cupo}).scalar_one()

        assert float(saldo) == 30
        assert cantidad_despachos == 1

    finally:
        test_db_session.execute(text("""
            DELETE FROM alerta_despacho
            WHERE id_alerta IN (
                SELECT id_alerta
                FROM alertas
                WHERE id_vehiculo = :vehiculo
            )
        """), {"vehiculo": id_vehiculo})

        test_db_session.execute(text("""
            DELETE FROM alertas
            WHERE id_vehiculo = :vehiculo
        """), {"vehiculo": id_vehiculo})

        for id_despacho in id_despachos:
            test_db_session.execute(text("""
                DELETE FROM auditoria
                WHERE entidad = 'despachos'
                  AND id_registro = :id
            """), {"id": id_despacho})

        test_db_session.execute(text("""
            DELETE FROM despachos
            WHERE id_cupo = :id
        """), {"id": id_cupo})

        test_db_session.execute(text("""
            DELETE FROM cupos WHERE id_cupo = :id
        """), {"id": id_cupo})

        test_db_session.execute(text("""
            DELETE FROM vehiculos WHERE id_vehiculo = :id
        """), {"id": id_vehiculo})

        test_db_session.commit()
def test_despacho_repetido_con_misma_clave_no_duplica(test_db_session):
    from datetime import date, timedelta
    from uuid import uuid4
    from sqlalchemy import text

    # Crear vehículo exclusivo para la prueba
    placa = f"IDEM-{uuid4().hex[:8].upper()}"

    vehiculo = test_db_session.execute(text("""
        INSERT INTO vehiculos (placa, descripcion)
        VALUES (:placa, 'Vehículo temporal para prueba de idempotencia')
        RETURNING id_vehiculo
    """), {"placa": placa}).mappings().one()

    id_vehiculo = vehiculo["id_vehiculo"]

    # Crear cupo con 100 litros
    cupo = test_db_session.execute(text("""
        INSERT INTO cupos (
            id_vehiculo,
            cantidad_autorizada,
            saldo_disponible,
            fecha_inicio,
            fecha_fin,
            estado
        )
        VALUES (:vehiculo, 100, 100, :inicio, :fin, 'VIGENTE')
        RETURNING id_cupo
    """), {
        "vehiculo": id_vehiculo,
        "inicio": date.today(),
        "fin": date.today() + timedelta(days=30)
    }).mappings().one()

    id_cupo = cupo["id_cupo"]
    test_db_session.commit()

    clave = str(uuid4())
    id_despacho = None

    try:
        token = login(
            "operador1@controldiesel.test",
            "Operador1#2026"
        ).json()["access_token"]

        datos = {
            "id_cupo": id_cupo,
            "cantidad": 20,
            "idempotency_key": clave
        }

        # Primera solicitud
        primera = client.post(
            "/despachos/",
            json=datos,
            headers=auth(token)
        )

        assert primera.status_code == 201, primera.text
        id_despacho = primera.json()["id_despacho"]

        # Repetir exactamente la misma solicitud
        segunda = client.post(
            "/despachos/",
            json=datos,
            headers=auth(token)
        )

        assert segunda.status_code == 200, segunda.text
        assert segunda.json()["id_despacho"] == id_despacho

        # Comprobar que solo existe un despacho
        cantidad_despachos = test_db_session.execute(text("""
            SELECT COUNT(*)
            FROM despachos
            WHERE id_cupo = :cupo
              AND idempotency_key = :clave
        """), {
            "cupo": id_cupo,
            "clave": clave
        }).scalar_one()

        assert cantidad_despachos == 1

        # Comprobar que el saldo solo se descontó una vez
        saldo = test_db_session.execute(text("""
            SELECT saldo_disponible
            FROM cupos
            WHERE id_cupo = :cupo
        """), {"cupo": id_cupo}).scalar_one()

        assert float(saldo) == 80

    finally:
        if id_despacho is not None:
            test_db_session.execute(text("""
                DELETE FROM auditoria
                WHERE entidad = 'despachos'
                  AND id_registro = :id
            """), {"id": id_despacho})

            test_db_session.execute(text("""
                DELETE FROM despachos
                WHERE id_despacho = :id
            """), {"id": id_despacho})

        test_db_session.execute(text("""
            DELETE FROM cupos WHERE id_cupo = :id
        """), {"id": id_cupo})

        test_db_session.execute(text("""
            DELETE FROM vehiculos WHERE id_vehiculo = :id
        """), {"id": id_vehiculo})

        test_db_session.commit()
def test_misma_clave_con_cantidad_diferente_devuelve_409(test_db_session):
    from datetime import date, timedelta
    from uuid import uuid4

    # Crear un vehículo exclusivo para esta prueba.
    placa = f"ID{uuid4().hex[:8].upper()}"

    vehiculo = test_db_session.execute(text("""
        INSERT INTO vehiculos (placa, descripcion)
        VALUES (:placa, 'Vehículo temporal para prueba de idempotencia')
        RETURNING id_vehiculo
    """), {
        "placa": placa
    }).mappings().one()

    id_vehiculo = vehiculo["id_vehiculo"]

    # Crear un cupo vigente con 100 litros.
    cupo = test_db_session.execute(text("""
        INSERT INTO cupos (
            id_vehiculo,
            cantidad_autorizada,
            saldo_disponible,
            fecha_inicio,
            fecha_fin,
            estado
        )
        VALUES (
            :vehiculo,
            100,
            100,
            :inicio,
            :fin,
            'VIGENTE'
        )
        RETURNING id_cupo
    """), {
        "vehiculo": id_vehiculo,
        "inicio": date.today(),
        "fin": date.today() + timedelta(days=30)
    }).mappings().one()

    id_cupo = cupo["id_cupo"]
    clave = str(uuid4())
    id_despacho = None

    test_db_session.commit()

    try:
        # Usar el helper login() que ya existe al inicio de este archivo.
        respuesta_login = login(
            "operador1@controldiesel.test",
            "Operador1#2026"
        )
        assert respuesta_login.status_code == 200, respuesta_login.text

        token = respuesta_login.json()["access_token"]
        headers = auth(token)

        # Primera solicitud: registra 20 litros.
        primera = client.post(
            "/despachos/",
            json={
                "id_cupo": id_cupo,
                "cantidad": 20,
                "idempotency_key": clave
            },
            headers=headers
        )

        assert primera.status_code == 201, primera.text
        id_despacho = primera.json()["id_despacho"]

        # Segunda solicitud: misma clave, pero intenta registrar 30 litros.
        segunda = client.post(
            "/despachos/",
            json={
                "id_cupo": id_cupo,
                "cantidad": 30,
                "idempotency_key": clave
            },
            headers=headers
        )

        assert segunda.status_code == 409, segunda.text
        assert "clave de idempotencia" in segunda.json()["detail"].lower()

        # Debe existir un solo despacho asociado a esa clave.
        cantidad_despachos = test_db_session.execute(text("""
            SELECT COUNT(*)
            FROM despachos
            WHERE id_cupo = :cupo
              AND idempotency_key = :clave
        """), {
            "cupo": id_cupo,
            "clave": clave
        }).scalar_one()

        assert cantidad_despachos == 1

        # El saldo debe haberse descontado una sola vez: 100 - 20 = 80.
        saldo = test_db_session.execute(text("""
            SELECT saldo_disponible
            FROM cupos
            WHERE id_cupo = :cupo
        """), {
            "cupo": id_cupo
        }).scalar_one()

        assert float(saldo) == 80

    finally:
        # Eliminar solamente los registros creados por esta prueba.
        if id_despacho is not None:
            test_db_session.execute(text("""
                DELETE FROM auditoria
                WHERE entidad = 'despachos'
                  AND id_registro = :id
            """), {"id": id_despacho})

            test_db_session.execute(text("""
                DELETE FROM despachos
                WHERE id_despacho = :id
            """), {"id": id_despacho})

        test_db_session.execute(text("""
            DELETE FROM cupos
            WHERE id_cupo = :id
        """), {"id": id_cupo})

        test_db_session.execute(text("""
            DELETE FROM vehiculos
            WHERE id_vehiculo = :id
        """), {"id": id_vehiculo})

        test_db_session.commit()
