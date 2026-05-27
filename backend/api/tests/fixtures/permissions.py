from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def auth_service_mock():
    return AsyncMock()


@pytest.fixture
def rbac_service_mock():
    return AsyncMock()
