from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings


class Base(DeclarativeBase):
    pass


# Движок подключения к БД
engine = create_async_engine(settings.db.database_url, echo=False)

# Фабрика асинхронных сессий БД
async_session_maker = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Провайдер сессии БД для FastAPI Depends.
    Открывает сессию, отдаёт её, закрывает после завершения запроса.

    Yields:
        Активная асинхронная сессия БД
    """
    async with async_session_maker() as session:
        yield session


@asynccontextmanager
async def get_repository[T](repo_class: type[T]) -> AsyncGenerator[T, None]:
    """
    Контекстный менеджер для быстрой работы с БД.
    Сам открывает сессию, создает репозиторий и закрывает всё за собой.

    Yields:
        Экземпляр репозитория repo_class с активной сессией
    """
    async with async_session_maker() as session:
        yield repo_class(session=session)
