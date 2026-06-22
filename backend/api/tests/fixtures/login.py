import jwt
import pytest

from backend.api.tests.test_permissions import TEST_ALGO, TEST_SECRET


@pytest.fixture
def valid_user_creds():
    return {"username": "admin@admin.com", "password": "admin"}


@pytest.fixture
def valid_token():
    return jwt.encode({"sub": "1"}, TEST_SECRET, algorithm=TEST_ALGO)
