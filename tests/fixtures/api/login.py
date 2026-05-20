import pytest


@pytest.fixture
def valid_user_creds():
    return {"username": "admin@admin.com", "password": "admin"}
