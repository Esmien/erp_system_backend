import pytest

from backend.team.repository import TeamRepository
from backend.team.service import TeamService


@pytest.fixture
def team_repo(db_session):
    return TeamRepository(session=db_session)


@pytest.fixture
def team_service(mock_uow):
    return TeamService(uow=mock_uow)
