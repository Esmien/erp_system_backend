from backend.core.enums import TaskStatus


async def test_create_task(task_repo, task_in):
    created_task = await task_repo.create(**task_in.model_dump(), author_id=1)

    assert created_task.id is not None
    assert created_task.title == task_in.title
    assert created_task.author_id == 1
    assert created_task.status == TaskStatus.OPEN


async def test_get_task_by_id(task_repo, task_in):
    created_task = await task_repo.create(**task_in.model_dump(), author_id=1)
    found_task = await task_repo.get_by_id(obj_id=created_task.id)

    assert found_task is not None
    assert found_task.id == created_task.id
    assert found_task.title == task_in.title


async def test_get_task_not_found(task_repo):
    found_task = await task_repo.get_by_id(obj_id=9999)
    assert found_task is None


async def test_update_task(task_repo, task_in):
    task = await task_repo.create(**task_in.model_dump(), author_id=1)

    update_data = {"title": "Новое название", "status": TaskStatus.IN_PROGRESS}
    updated_task = await task_repo.update(obj_id=task.id, update_data=update_data)

    assert updated_task.title == "Новое название"
    assert updated_task.status == TaskStatus.IN_PROGRESS


async def test_delete_task(task_repo, task_in):
    task = await task_repo.create(**task_in.model_dump(), author_id=1)

    await task_repo.delete(obj_id=task.id)

    deleted_task = await task_repo.get_by_id(obj_id=task.id)
    assert deleted_task is None


async def test_get_tasks_with_filters_status_and_user(task_repo, task_in):
    """Покрываем строки фильтрации по status и user_id"""
    await task_repo.create(**task_in.model_dump(), author_id=1)

    tasks, total = await task_repo.get_tasks_with_filters(offset=0, limit=20, user_id=1, task_status=TaskStatus.OPEN)
    assert len(tasks) >= 1


async def test_get_tasks_with_filters_team(task_repo):
    """Покрываем ветку elif team_id в репозитории"""
    # Достаточно просто вызвать метод, чтобы SQLAlchemy построил запрос с JOIN
    tasks, total = await task_repo.get_tasks_with_filters(offset=0, limit=20, team_id=1)
    assert isinstance(tasks, list)


async def test_update_task_not_found_repo(task_repo):
    """Покрываем ранний возврат (None), если обновляемой задачи нет"""
    updated = await task_repo.update(obj_id=99999, update_data={"title": "Призрак"})
    assert updated is None


async def test_delete_task_not_found_repo(task_repo):
    """Покрываем ранний возврат, если удаляемой задачи нет"""
    # Если возвращает None и не падает с ошибкой — тест пройден
    await task_repo.delete(obj_id=99999)
