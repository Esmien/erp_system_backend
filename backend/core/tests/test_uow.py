from unittest.mock import patch

from backend.api.dependencies.uow import get_uow
from backend.core.uow import UnitOfWork


def test_uow_provider():
    result = get_uow()

    assert type(result) is UnitOfWork


async def test_uow_aenter_aexit_success(mock_session_factory):
    """Тест успешного прохождения контекстного менеджера"""
    factory_mock, session_mock = mock_session_factory
    with patch("backend.core.uow.async_session_maker", factory_mock):
        uow = UnitOfWork()

        async with uow:
            # Проверяем, что фабрика сессий была вызвана при входе в контекст
            factory_mock.assert_called_once()

            # Убеждаемся, что все репозитории были инициализированы
            assert uow.users is not None
            assert uow.auth is not None
            assert uow.register is not None
            assert uow.teams is not None
            assert uow.tasks is not None
            assert uow.rbac is not None

        # После успешного выхода (без исключений) сессия должна закрыться,
        # а автоматический rollback вызываться не должен
        session_mock.close.assert_called_once()
        session_mock.rollback.assert_not_called()


async def test_uow_aexit_with_exception(mock_session_factory):
    """Тест автоматического отката (rollback) при исключении внутри контекста"""
    factory_mock, session_mock = mock_session_factory

    with patch("backend.core.uow.async_session_maker", factory_mock):
        uow = UnitOfWork()

        try:
            async with uow:
                # Имитируем падение кода внутри бизнес-логики
                raise ValueError("Test error inside UoW")
        except ValueError:
            pass

        # При ошибке __aexit__ должен сначала сделать rollback, а затем close
        session_mock.rollback.assert_called_once()
        session_mock.close.assert_called_once()


async def test_uow_commit_method(mock_session_factory):
    """Тест явного вызова метода commit"""
    factory_mock, session_mock = mock_session_factory

    with patch("backend.core.uow.async_session_maker", factory_mock):
        uow = UnitOfWork()
        async with uow:
            await uow.commit()

        # Проверяем, что вызов uow.commit() прокинулся в session.commit()
        session_mock.commit.assert_called_once()


async def test_uow_rollback_method(mock_session_factory):
    """Тест явного вызова метода rollback"""
    factory_mock, session_mock = mock_session_factory

    with patch("backend.core.uow.async_session_maker", factory_mock):
        uow = UnitOfWork()
        async with uow:
            await uow.rollback()

        # Проверяем, что вызов uow.rollback() прокинулся в session.rollback()
        session_mock.rollback.assert_called_once()
