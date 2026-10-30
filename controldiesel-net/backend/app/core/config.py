
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ControlDiesel-Net API"
    VERSION: str = "1.0.0"

    DATABASE_URL: str
    secret_key: str = "CAMBIAR_EN_EL_ARCHIVO_ENV"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def cors_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
        ]


settings = Settings()
