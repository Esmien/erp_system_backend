from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseModelConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class LoggerConfig(BaseModelConfig):
    LOG_LEVEL: str = "DEBUG"
    LOG_SERIALIZE: bool = True  # Если True, будет писать в JSON


class SecurityConfig(BaseModelConfig):
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


class DatabaseConfig(BaseModelConfig):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_TEST_HOST: str = "localhost"
    DB_PORT: int
    DB_NAME: str
    TEST_DB_NAME: str

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def test_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_TEST_HOST}:{self.DB_PORT}/{self.TEST_DB_NAME}"


class RedisConfig(BaseModelConfig):
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0
    CACHE_TTL: int = 3600

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


class RabbitMQConfig(BaseModelConfig):
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int

    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"


class RedisKeys(BaseModelConfig):
    KEY_OF_SYSTEM_TOKEN: str  # ключ в хранилище redis, по которому лежит системный токен

    @staticmethod
    def key_jwt_blacklist(jti: str) -> str:
        return f"backend:jwt:blacklist:{jti}"

    @staticmethod
    def key_jwt_access(tg_id: int) -> str:
        return f"backend:jwt:access:{tg_id}"

    @staticmethod
    def key_jwt_refresh(tg_id: int) -> str:
        return f"backend:jwt:refresh:{tg_id}"

    @staticmethod
    def key_reg_code(code: str) -> str:
        return f"backend:reg_code:{code}"

    @staticmethod
    def key_rbac_rule(role_id: int, business_element_name: str) -> str:
        return f"backend:rbac:rule:{role_id}:{business_element_name}"


class InviteCodeConfig(BaseModelConfig):
    CODE_LENGTH: int = 6


class SentryConfig(BaseModelConfig):
    ENABLED: bool = False
    DSN: str = ""

    @model_validator(mode="after")
    def check_dsn_if_enabled(self):
        # Если Sentry включен, но DSN пустой — падаем с понятной ошибкой
        if self.ENABLED and not self.DSN:
            raise ValueError("Sentry включен, но не задан DSN. Проверьте переменные окружения (.env)")
        return self


class Settings(BaseModelConfig):
    db: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    rabbitmq: RabbitMQConfig = RabbitMQConfig()
    redis_keys: RedisKeys = RedisKeys()
    inv_code: InviteCodeConfig = InviteCodeConfig()
    logger: LoggerConfig = LoggerConfig()
    security: SecurityConfig = SecurityConfig()
    sentry_conf: SentryConfig = SentryConfig()


settings = Settings()
