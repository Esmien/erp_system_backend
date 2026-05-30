import pytest

from backend.core.constants import RoleName, TaskStatus
from backend.task.schemas import (
    TaskRead,
    TaskCreate,
    TaskUpdate,
    TaskChangeStatus,
)
from backend.exceptions import (
    TaskDoesNotExistsError,
    AccessDeniedError,
    TeamDoesNotExistsError,
    UserDoesNotExistsError,
)


async def test_get_task_success(task_service, mock_uow, sample_task):
    mock_uow.tasks.get_task_by_id.return_value = sample_task

    result = await task_service.get_task(task_id=1)

    assert result.id == 1
    mock_uow.tasks.get_task_by_id.assert_called_once_with(1)


async def test_get_task_not_found(task_service, mock_uow):
    mock_uow.tasks.get_task_by_id.return_value = None

    with pytest.raises(TaskDoesNotExistsError):
        await task_service.get_task(task_id=999)


async def test_create_task(task_service, mock_uow, mock_user_author, sample_task):
    task_in = TaskCreate(title="Тест")
    mock_uow.tasks.create_task.return_value = sample_task

    result = await task_service.create_task(task_in=task_in, author=mock_user_author)

    assert result.title == "Тест"
    mock_uow.tasks.create_task.assert_called_once_with(
        task_in=task_in, author_id=mock_user_author.id
    )
    mock_uow.commit.assert_called_once()


async def test_update_task_access_denied(
    task_service, mock_uow, mock_user_stranger, sample_task
):
    # Пытаемся обновить чужую задачу без прав менеджера/админа
    mock_uow.tasks.get_task_by_id.return_value = sample_task
    update_data = TaskUpdate(title="Взлом")

    with pytest.raises(AccessDeniedError):
        await task_service.update_task(
            task_id=1, update_data=update_data, user=mock_user_stranger
        )


async def test_update_task_success(
    task_service, mock_uow, mock_user_author, sample_task
):
    # Автор имеет право обновить свою задачу
    mock_uow.tasks.get_task_by_id.return_value = sample_task

    updated_task_read = TaskRead(**sample_task.model_dump())
    updated_task_read.title = "Обновлено"
    mock_uow.tasks.update_task.return_value = updated_task_read

    update_data = TaskUpdate(title="Обновлено")
    result = await task_service.update_task(
        task_id=1, update_data=update_data, user=mock_user_author
    )

    assert result.title == "Обновлено"
    mock_uow.commit.assert_called_once()


async def test_delete_task_success(
    task_service, mock_uow, mock_user_author, sample_task
):
    mock_uow.tasks.get_task_by_id.return_value = sample_task

    await task_service.delete_task(task_id=1, user=mock_user_author)

    mock_uow.tasks.delete_task.assert_called_once_with(task_id=1)
    mock_uow.commit.assert_called_once()


async def test_get_filtered_tasks_team_scope(task_service, mock_uow, mock_user_author):
    mock_user_author.team_id = 1
    mock_uow.tasks.get_tasks_with_filters.return_value = []

    result = await task_service.get_filtered_tasks(
        user=mock_user_author, scope="team", task_status=None
    )
    assert result == []
    mock_uow.tasks.get_tasks_with_filters.assert_called_once_with(
        user_id=None, team_id=1, task_status=None
    )


async def test_get_filtered_tasks_team_scope_no_team(
    task_service, mock_uow, mock_user_author
):
    mock_user_author.team_id = None
    with pytest.raises(TeamDoesNotExistsError):
        await task_service.get_filtered_tasks(
            user=mock_user_author, scope="team", task_status=None
        )


async def test_get_filtered_tasks_all_scope_admin(
    task_service, mock_uow, mock_user_author
):
    mock_user_author.role.name = RoleName.ADMIN
    mock_uow.tasks.get_tasks_with_filters.return_value = []

    result = await task_service.get_filtered_tasks(
        user=mock_user_author, scope="all", task_status=None
    )
    assert result == []


async def test_update_task_empty_dict(
    task_service, mock_uow, mock_user_author, sample_task
):
    mock_uow.tasks.get_task_by_id.return_value = sample_task
    # Пустой update_data
    update_data = TaskUpdate()

    result = await task_service.update_task(
        task_id=1, update_data=update_data, user=mock_user_author
    )
    # Должен сразу вернуть текущую задачу без вызова репозитория
    assert result == sample_task
    mock_uow.tasks.update_task.assert_not_called()


async def test_update_task_invalid_executor(
    task_service, mock_uow, mock_user_author, sample_task
):
    mock_uow.tasks.get_task_by_id.return_value = sample_task
    # Имитируем, что юзер для назначения не найден
    mock_uow.auth.get_user_and_role_by_user_id.return_value = None
    update_data = TaskUpdate(executor_id=999)

    with pytest.raises(UserDoesNotExistsError):
        await task_service.update_task(
            task_id=1, update_data=update_data, user=mock_user_author
        )


async def test_update_task_repo_fails(
    task_service, mock_uow, mock_user_author, sample_task
):
    mock_uow.tasks.get_task_by_id.return_value = sample_task
    # Имитируем, что задача пропала из БД прямо во время обновления
    mock_uow.tasks.update_task.return_value = None
    update_data = TaskUpdate(title="Test")

    with pytest.raises(TaskDoesNotExistsError):
        await task_service.update_task(
            task_id=1, update_data=update_data, user=mock_user_author
        )


async def test_change_status_success(
    task_service, mock_uow, mock_user_author, sample_task
):
    mock_uow.tasks.get_task_by_id.return_value = sample_task
    mock_uow.tasks.update_task.return_value = sample_task
    new_status = TaskChangeStatus(status=TaskStatus.DONE)

    result = await task_service.change_status(
        task_id=1, new_status=new_status, user=mock_user_author
    )
    assert result == sample_task


async def test_change_status_access_denied(
    task_service, mock_uow, mock_user_stranger, sample_task
):
    mock_uow.tasks.get_task_by_id.return_value = sample_task
    new_status = TaskChangeStatus(status=TaskStatus.DONE)

    with pytest.raises(AccessDeniedError):
        await task_service.change_status(
            task_id=1, new_status=new_status, user=mock_user_stranger
        )


async def test_change_status_task_not_found(task_service, mock_uow, mock_user_author):
    mock_uow.tasks.get_task_by_id.return_value = None
    new_status = TaskChangeStatus(status=TaskStatus.DONE)

    with pytest.raises(TaskDoesNotExistsError):
        await task_service.change_status(
            task_id=1, new_status=new_status, user=mock_user_author
        )


async def test_delete_task_not_found(task_service, mock_uow, mock_user_author):
    mock_uow.tasks.get_task_by_id.return_value = None
    with pytest.raises(TaskDoesNotExistsError):
        await task_service.delete_task(task_id=999, user=mock_user_author)


async def test_get_filtered_tasks_my_scope(task_service, mock_uow, mock_user_author):
    """Покрываем ветку if scope == 'my'"""
    mock_uow.tasks.get_tasks_with_filters.return_value = []

    result = await task_service.get_filtered_tasks(
        user=mock_user_author, scope="my", task_status=None
    )

    assert result == []
    mock_uow.tasks.get_tasks_with_filters.assert_called_once_with(
        user_id=mock_user_author.id, team_id=None, task_status=None
    )


async def test_change_status_repo_fails(
    task_service, mock_uow, mock_user_author, sample_task
):
    """Покрываем исключение, когда репозиторий вернул None при обновлении статуса"""
    mock_uow.tasks.get_task_by_id.return_value = sample_task
    mock_uow.tasks.update_task.return_value = None
    new_status = TaskChangeStatus(status=TaskStatus.DONE)

    with pytest.raises(TaskDoesNotExistsError):
        await task_service.change_status(
            task_id=1, new_status=new_status, user=mock_user_author
        )


async def test_update_task_not_found_initially(
    task_service, mock_uow, mock_user_author
):
    """
    Покрываем исключение в update_task, когда задача не найдена
    в самом начале проверки (до обновления в БД).
    """
    # Обязательно передаем какие-то данные, чтобы не сработал
    # ранний return для пустого update_dict
    update_data = TaskUpdate(title="Попытка обновления")

    # Репозиторий возвращает None — задачи нет
    mock_uow.tasks.get_task_by_id.return_value = None

    with pytest.raises(TaskDoesNotExistsError):
        await task_service.update_task(
            task_id=999, update_data=update_data, user=mock_user_author
        )
