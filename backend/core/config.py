from enum import StrEnum

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RoleName(StrEnum):
    USER = "user"
    ADMIN = "admin"
    MANAGER = "manager"


class Settings(BaseSettings):
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database (Postgres)
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "business_management"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """
        Собираем строку подключения автоматически из переменных.
        Используем asyncpg драйвер.
        """
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Uvicorn
    UVI_PORT: int = 8000
    UVI_HOST: str = "0.0.0.0"

    # Loguru
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "<green>{time:HH:mm}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
    LOG_COLORIZE: bool = True

    # Конфигурация Pydantic
    model_config = SettingsConfigDict(
        env_file=".env",  # Читаем из .env
        env_file_encoding="utf-8",
        extra="ignore",  # Игнорируем лишние переменные в .env
    )


# Создаем единственный экземпляр настроек
settings = Settings()
