from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

from backend.core.config import settings
from backend.api.v1.routers.auth import router as auth_router
from backend.api.v1.routers.teams import router as teams_router
from backend.api.v1.routers.users import router as users_router
from backend.core.logger import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения
    """
    setup_logger()
    logger.info("API запущено, логгер сконфигурирован")
    logger.info(f"Подключение к БД: {settings.db.database_url.split('@')[-1]}")

    yield

    logger.info("🛑 Сервис остановлен")


app = FastAPI(
    title="Business Management Platform",
    version="0.1.0",
    lifespan=lifespan,
    openapi_prefix="/api/v1",
)

# Подключаем роутеры
app.include_router(auth_router)
app.include_router(teams_router)
app.include_router(users_router)
