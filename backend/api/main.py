from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqladmin import Admin

from backend.admin.security import AdminAuth
from backend.admin.views import TaskAdmin, TeamAdmin, UserAdmin
from backend.api.exception_handlers import setup_exception_handlers
from backend.api.v1.routers.auth import router as auth_router
from backend.api.v1.routers.calendar import router as calendar_router
from backend.api.v1.routers.comments import router as comments_router
from backend.api.v1.routers.evaluations import router as evaluations_router
from backend.api.v1.routers.meetings import router as meetings_router
from backend.api.v1.routers.tasks import router as tasks_router
from backend.api.v1.routers.teams import router as teams_router
from backend.api.v1.routers.users import router as users_router
from backend.core.config import settings
from backend.core.database.engine import engine
from backend.core.database.redis import close_redis
from backend.core.logger import setup_logger

if settings.sentry_conf.ENABLED:
    sentry_sdk.init(
        dsn=settings.sentry_conf.DSN,
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=True,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=1.0,
        # Set profile_session_sample_rate to 1.0 to profile 100%
        # of profile sessions.
        profile_session_sample_rate=1.0,
        # Set profile_lifecycle to "trace" to automatically
        # run the profiler on when there is an active transaction
        profile_lifecycle="trace",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет жизненным циклом приложения
    """
    setup_logger()
    logger.info("API запущено, логгер сконфигурирован")
    logger.info(f"Подключение к БД: {settings.db.database_url.split('@')[-1]}")

    yield

    await close_redis()
    logger.info("🛑 Сервис остановлен")


middleware = [
    Middleware(
        CORSMiddleware,  # type: ignore
        allow_origins=["http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]


app = FastAPI(
    title="Business Management Platform",
    middleware=middleware,
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

authentication_backend = AdminAuth(secret_key=settings.security.SECRET_KEY)
admin = Admin(
    app=app,
    engine=engine,
    authentication_backend=authentication_backend,
    title="Административная панель Business Management Platform",
)

admin.add_view(UserAdmin)
admin.add_view(TeamAdmin)
admin.add_view(TaskAdmin)
