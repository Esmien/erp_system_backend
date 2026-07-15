import pytest

from backend.core.utils.error_schemas import ErrorResponseSchema
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


@pytest.fixture
def response_get_team_by_id():
    return {
        "name": "Dummy name",
        "description": None,
        "id": 1,
        "invite_code": "111111",
        "members": [],
    }


@pytest.fixture
def request_body_for_create_team():
    return {"name": "New Team"}


@pytest.fixture
def response_data_by_create_team():
    return {"name": "New Team", "description": None, "id": 2}


@pytest.fixture
def request_duplicate():
    return {"name": "Dummy name"}


@pytest.fixture
def response_data_duplicate():
    content = ErrorResponseSchema(detail="Команда с таким названием уже существует", status_code=400)
    return content.model_dump()


@pytest.fixture
def join_team_right_code_request():
    return {"invite_code": "111111"}


@pytest.fixture
def join_team_wrong_code_request():
    return {"invite_code": "222222"}


@pytest.fixture
def join_team_success_response():
    return {"name": "Dummy name", "description": None, "id": 1, "invite_code": "111111"}


@pytest.fixture
def join_team_already_exists_response():
    content = ErrorResponseSchema(detail="Вы уже состоите в команде", status_code=400)
    return content.model_dump()


@pytest.fixture
def join_team_wrong_code_response():
    content = ErrorResponseSchema(detail="Команда с таким кодом не найдена", status_code=404)
    return content.model_dump()
