from unittest.mock import AsyncMock

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
def rbac_service(mock_uow):
    return RbacService(uow=mock_uow)


@pytest.fixture
def rbac_repo(db_session):
    return RbacRepository(session=db_session)
