from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.rbac.repository import RbacRepository
from backend.rbac.service import RbacService


@pytest.fixture
def mock_rbac_service():
    """Мок для проверки динамических прав"""
    service = AsyncMock(spec=RbacService)
    service.check_permission.return_value = True
    return service


@pytest.fixture
def rbac_service(mock_uow, mock_redis):
    return RbacService(uow=mock_uow, redis=mock_redis)


@pytest.fixture
def rbac_repo(db_session):
    return RbacRepository(session=db_session)


@pytest.fixture
def auth_service_mock():
    return AsyncMock()


@pytest.fixture
def rbac_service_mock(rbac_service):
    return rbac_service


@pytest.fixture
def mock_creds():
    return MagicMock()
