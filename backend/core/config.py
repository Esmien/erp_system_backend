from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseModelConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class LoggerConfig(BaseModelConfig):
    LOG_LEVEL: str = "DEBUG"
    LOG_SERIALIZE: bool = False  # Если True, будет писать в JSON


class SecurityConfig(BaseModelConfig):
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


class DatabaseConfig(BaseModelConfig):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class RedisConfig(BaseModelConfig):
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"


class InviteCodeConfig(BaseModelConfig):
    CODE_LENGTH: int = 6


class Settings(BaseModelConfig):
    db: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    inv_code: InviteCodeConfig = InviteCodeConfig()
    logger: LoggerConfig = LoggerConfig()
    security: SecurityConfig = SecurityConfig()


settings = Settings()
