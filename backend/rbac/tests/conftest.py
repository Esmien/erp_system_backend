import pytest

from backend.rbac.repository import RbacRepository
from backend.rbac.service import RbacService


@pytest.fixture
def rbac_service(mock_uow):
    return RbacService(uow=mock_uow)


@pytest.fixture
def rbac_repo(db_session):
    return RbacRepository(session=db_session)
