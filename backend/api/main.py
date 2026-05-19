import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

from backend.core.config import settings
from backend.api.v1.routers.auth import router as auth_router
from backend.api.v1.routers.teams import router as teams_router
from backend.api.v1.routers.users import router as users_router


def setup_logging():
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        colorize=settings.LOG_COLORIZE,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("🚀 API запущено, логгер сконфигурирован")
    logger.info(f"Подключение к БД: {settings.DATABASE_URL.split('@')[-1]}")

    yield

    logger.info("🛑 Сервис остановлен")


app = FastAPI(
    title="Business Management Platform",
    version="0.1.0",
    lifespan=lifespan,
    openapi_prefix="/api/v1",
)

# Подключаем роутер
app.include_router(auth_router)
app.include_router(teams_router)
app.include_router(users_router)
