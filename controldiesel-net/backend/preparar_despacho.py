from pathlib import Path
from datetime import date, timedelta

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, text


class TestSettings(BaseSettings):
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent / ".env.test",
        extra="ignore"
    )


settings = TestSettings()
engine = create_engine(settings.DATABASE_URL)

hoy = date.today()

with engine.begin() as db:
    # Crear un vehículo exclusivo para esta prueba
    vehiculo = db.execute(text("""
        INSERT INTO vehiculos (placa, descripcion)
        VALUES (:placa, 'Vehículo temporal para pruebas de despacho')
        RETURNING id_vehiculo
    """), {
        "placa": f"TEST-{date.today().strftime('%Y%m%d')}"
    }).mappings().one()

    id_vehiculo = vehiculo["id_vehiculo"]

    # Crear un cupo vigente por 30 días
    cupo = db.execute(text("""
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
        "inicio": hoy,
        "fin": hoy + timedelta(days=30)
    }).mappings().one()

    print("Vehículo creado:", id_vehiculo)
    print("Cupo creado:", cupo["id_cupo"])
    print("Saldo disponible: 100 litros")