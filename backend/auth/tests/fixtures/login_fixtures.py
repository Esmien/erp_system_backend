import jwt
import pytest

from backend.auth.repository import AuthRepository
from backend.auth.service import AuthService
from backend.rbac.tests.test_permissions import TEST_ALGO, TEST_SECRET


@pytest.fixture
def auth_repo(db_session):
    return AuthRepository(session=db_session)


@pytest.fixture
def auth_service(mock_uow, mock_redis):
    return AuthService(uow=mock_uow, redis=mock_redis)


@pytest.fixture
def valid_user_creds():
    return {"username": "admin@admin.com", "password": "admin"}


@pytest.fixture
def valid_token():
    return jwt.encode({"sub": "1"}, TEST_SECRET, algorithm=TEST_ALGO)
