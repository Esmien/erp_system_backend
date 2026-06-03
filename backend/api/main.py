from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

from backend.api.exception_handlers import setup_exception_handlers
from backend.core.config import settings
from backend.api.v1.routers.auth import router as auth_router
from backend.api.v1.routers.teams import router as teams_router
from backend.api.v1.routers.users import router as users_router
from backend.api.v1.routers.tasks import router as tasks_router
from backend.api.v1.routers.comments import router as comments_router
from backend.api.v1.routers.evaluations import router as evaluations_router
from backend.api.v1.routers.meetings import router as meetings_router
from backend.api.v1.routers.calendar import router as calendar_router
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
)

# Подключаем роутеры
app.include_router(router=auth_router, prefix="/api/v1")
app.include_router(router=teams_router, prefix="/api/v1")
app.include_router(router=users_router, prefix="/api/v1")
app.include_router(router=tasks_router, prefix="/api/v1")
app.include_router(router=comments_router, prefix="/api/v1")
app.include_router(router=evaluations_router, prefix="/api/v1")
app.include_router(router=meetings_router, prefix="/api/v1")
app.include_router(router=calendar_router, prefix="/api/v1")

setup_exception_handlers(app=app)
