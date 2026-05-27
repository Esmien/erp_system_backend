import pytest

from backend.core.constants import TaskStatus


@pytest.fixture
def task_in():
    return {
        "title": "Настроить CI/CD",
        "description": "Дописать Github Actions для деплоя",
        "expire": "2026-12-31",
        "status": TaskStatus.OPEN,
    }
