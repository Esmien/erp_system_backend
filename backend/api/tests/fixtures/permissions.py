from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def auth_service_mock():
    return AsyncMock()


@pytest.fixture
def rbac_service_mock(rbac_service):
    return rbac_service


@pytest.fixture
def mock_creds():
    return MagicMock()
