import pytest

from backend.core.config import settings


@pytest.fixture
def mock_settings():
    return settings
