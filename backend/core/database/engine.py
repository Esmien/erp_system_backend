from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False
)


async def get_session():
    async with async_session_maker() as session:
        yield session


@asynccontextmanager
async def get_repository[T](repo_class: type[T]) -> AsyncGenerator[T, None]:
    """
    Контекстный менеджер для быстрой работы с БД.
    Сам открывает сессию, создает репозиторий и закрывает всё за собой.

    Yields:
        Подключение к репозиторию с проброшенной сессией
    """
    async with async_session_maker() as session:
        yield repo_class(session)
