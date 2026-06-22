from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings


class Base(DeclarativeBase):
    pass


# Движок подключения к БД
engine = create_async_engine(settings.db.database_url, echo=False)

# Фабрика асинхронных сессий БД
async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


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
