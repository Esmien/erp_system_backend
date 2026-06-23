from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_settings():
    return MagicMock()
