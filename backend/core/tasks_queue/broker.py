import taskiq_fastapi
from loguru import logger
from taskiq import TaskiqEvents, TaskiqState
from taskiq_aio_pika import AioPikaBroker

from backend.core.config import settings

# Собираем URL для подключения
RABBITMQ_URL = settings.rabbitmq.rabbitmq_url

# Инициализируем правильный брокер
broker = AioPikaBroker(url=RABBITMQ_URL)

taskiq_fastapi.init(broker=broker, app_or_path="backend.api.main:app")


# --- События для Воркера (taskiq worker) ---
@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def worker_startup(state: TaskiqState) -> None:
    logger.info("🐰 Воркер подключился к RabbitMQ и готов к работе")


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def worker_shutdown(state: TaskiqState) -> None:
    logger.info("🔌 Воркер отключился от RabbitMQ")


# --- События для Клиента (FastAPI) ---
@broker.on_event(TaskiqEvents.CLIENT_STARTUP)
async def client_startup(state: TaskiqState) -> None:
    logger.info("📤 FastAPI-клиент установил соединение с RabbitMQ")


@broker.on_event(TaskiqEvents.CLIENT_SHUTDOWN)
async def client_shutdown(state: TaskiqState) -> None:
    logger.info("🔌 FastAPI-клиент разорвал соединение с RabbitMQ")
