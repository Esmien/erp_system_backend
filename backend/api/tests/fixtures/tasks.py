import pytest

from backend.core.enums import TaskStatus


@pytest.fixture
def task_in_json():
    return {
        "title": "Настроить CI/CD",
        "description": "Дописать Github Actions для деплоя",
        "expire": "2026-12-31",
    }


@pytest.fixture
def closed_task_json(task_in_json):
    return task_in_json | {"status": TaskStatus.DONE}


@pytest.fixture
def open_task_json(task_in_json):
    return task_in_json | {"status": TaskStatus.OPEN}
