from fastapi.testclient import TestClient
from app.main import app

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