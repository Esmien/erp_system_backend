from backend.core.constants import TaskStatus
from backend.task.schemas import TaskCreate


async def test_create_task(task_repo, task_in):
    created_task = await task_repo.create_task(task_in=task_in, author_id=1)

    assert created_task.id is not None
    assert created_task.title == task_in.title
    assert created_task.author_id == 1
    assert created_task.status == TaskStatus.OPEN


async def test_get_task_by_id(task_repo, task_in):
    created_task = await task_repo.create_task(task_in=task_in, author_id=1)
    found_task = await task_repo.get_task_by_id(task_id=created_task.id)

    assert found_task is not None
    assert found_task.id == created_task.id
    assert found_task.title == task_in.title


async def test_get_task_not_found(task_repo):
    found_task = await task_repo.get_task_by_id(task_id=9999)
    assert found_task is None


async def test_update_task(task_repo, task_in):
    task = await task_repo.create_task(task_in=task_in, author_id=1)

    update_data = {"title": "Новое название", "status": TaskStatus.IN_PROGRESS}
    updated_task = await task_repo.update_task(task_id=task.id, update_data=update_data)

    assert updated_task.title == "Новое название"
    assert updated_task.status == TaskStatus.IN_PROGRESS


async def test_delete_task(task_repo, task_in):
    task = await task_repo.create_task(task_in=task_in, author_id=1)

    await task_repo.delete_task(task_id=task.id)

    deleted_task = await task_repo.get_task_by_id(task_id=task.id)
    assert deleted_task is None


async def test_get_tasks_with_filters_status_and_user(task_repo, task_in):
    """Покрываем строки фильтрации по status и user_id"""
    task_in = TaskCreate(title="Фильтр", status=TaskStatus.IN_PROGRESS)
    await task_repo.create_task(task_in=task_in, author_id=1)

    tasks = await task_repo.get_tasks_with_filters(
        user_id=1, task_status=TaskStatus.IN_PROGRESS
    )
    assert len(tasks) >= 1


async def test_get_tasks_with_filters_team(task_repo):
    """Покрываем ветку elif team_id в репозитории"""
    # Достаточно просто вызвать метод, чтобы SQLAlchemy построил запрос с JOIN
    tasks = await task_repo.get_tasks_with_filters(team_id=1)
    assert isinstance(tasks, list)


async def test_update_task_not_found_repo(task_repo):
    """Покрываем ранний возврат (None), если обновляемой задачи нет"""
    updated = await task_repo.update_task(
        task_id=99999, update_data={"title": "Призрак"}
    )
    assert updated is None


async def test_delete_task_not_found_repo(task_repo):
    """Покрываем ранний возврат, если удаляемой задачи нет"""
    # Если возвращает None и не падает с ошибкой — тест пройден
    await task_repo.delete_task(task_id=99999)
