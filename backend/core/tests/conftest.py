from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_session_factory():
    """Создает мок для сессии и фабрики сессий"""
    session_mock = AsyncMock()
    factory_mock = MagicMock(return_value=session_mock)
    return factory_mock, session_mock
