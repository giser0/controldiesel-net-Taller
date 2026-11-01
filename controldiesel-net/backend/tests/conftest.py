from pathlib import Path

import pytest
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.main import app


# Cargar la configuración de la base de datos de pruebas
class TestSettings(BaseSettings):
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env.test",
        extra="ignore",
    )


test_settings = TestSettings()

# Crear la conexión exclusiva para las pruebas
test_engine = create_engine(test_settings.DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


# Sustituir la conexión normal por la de pruebas
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# Sesión disponible para las pruebas que necesiten preparar datos
@pytest.fixture
def test_db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()