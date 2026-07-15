from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator
from sqladmin import Admin

from backend.admin.security import AdminAuth
from backend.admin.views import TaskAdmin, TeamAdmin, UserAdmin
from backend.api.exception_handlers import setup_exception_handlers
from backend.auth.api.v1.auth_api import router as auth_router
from backend.auth.api.v1.register_code_api import router as reg_code_router
from backend.bot.api.bot_auth_router import router as bot_router
from backend.calendar.api.v1.calendar_api import router as calendar_router
from backend.comment.api.v1.comments_api import router as comments_router
from backend.core.config import settings
from backend.core.database.engine import engine
from backend.core.database.redis import close_redis
from backend.core.logger import setup_logger
from backend.core.tasks_queue.broker import broker
from backend.evaluation.api.v1.evaluations_api import router as evaluations_router
from backend.meeting.api.v1.meetings_api import router as meetings_router
from backend.task.api.v1.tasks_api import router as tasks_router
from backend.team.api.v1.teams_api import router as teams_router
from backend.user.api.v1.users_api import router as users_router

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

    if not broker.is_worker_process:
        await broker.startup()

    yield

    if not broker.is_worker_process:
        await broker.shutdown()

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

API_PREFIX = "/api/v1"

Instrumentator().instrument(app=app).expose(app=app, tags=["Мониторинг"])

# Подключаем роутеры
app.include_router(router=reg_code_router, prefix=API_PREFIX)
app.include_router(router=auth_router, prefix=API_PREFIX)
app.include_router(router=bot_router, prefix=API_PREFIX)
app.include_router(router=teams_router, prefix=API_PREFIX)
app.include_router(router=users_router, prefix=API_PREFIX)
app.include_router(router=tasks_router, prefix=API_PREFIX)
app.include_router(router=comments_router, prefix=API_PREFIX)
app.include_router(router=evaluations_router, prefix=API_PREFIX)
app.include_router(router=meetings_router, prefix=API_PREFIX)
app.include_router(router=calendar_router, prefix=API_PREFIX)

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
