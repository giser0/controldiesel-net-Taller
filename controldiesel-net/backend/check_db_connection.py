from sqlalchemy import create_engine, text
from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=".env.test",
        extra="ignore"
    )


settings = TestSettings()

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as connection:
    resultado = connection.execute(text("SELECT current_database()"))
    print("Base de datos conectada:", resultado.scalar())