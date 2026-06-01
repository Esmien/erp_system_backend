import pytest

from backend.team.repository import TeamRepository
from backend.team.service import TeamService
from backend.user.schemas import UserDTO


@pytest.fixture
def team_repo(db_session):
    return TeamRepository(session=db_session)


@pytest.fixture
def team_service(mock_uow, mock_rbac_service):
    return TeamService(uow=mock_uow, rbac_service=mock_rbac_service)


@pytest.fixture
def mock_user():
    return UserDTO(
        id=1,
        email="test@test.com",
        hashed_password="hash",
        name="Test",
        role_id=1,
        is_active=True,
        team_id=1,
    )
