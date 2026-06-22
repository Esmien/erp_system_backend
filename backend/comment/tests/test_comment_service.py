import pytest

from backend.api.dependencies.pagination import PaginationParams
from backend.comment.schemas import CommentCreate
from backend.core.enums import RoleName
from backend.exceptions import AccessDeniedError, TaskDoesNotExistError


async def test_add_comment_success(comment_service, mock_uow, mock_user_author, sample_task, sample_comment):
    # Имитируем найденную задачу
    mock_uow.tasks.get_by_id.return_value = sample_task
    # Имитируем успешное создание комментария в БД
    mock_uow.comments.create.return_value = sample_comment

    comment_in = CommentCreate(text="Тестовый комментарий")

    # Автор задачи оставляет комментарий
    result = await comment_service.add_comment(task_id=1, user=mock_user_author, comment_in=comment_in)

    assert result.text == "Тестовый комментарий"
    mock_uow.comments.create.assert_called_once_with(
        task_id=1, author_id=mock_user_author.id, text="Тестовый комментарий"
    )
    mock_uow.commit.assert_called_once()


async def test_add_comment_access_denied(comment_service, mock_uow, mock_user_stranger, sample_task):
    # Имитируем найденную задачу
    mock_uow.tasks.get_task_by_id.return_value = sample_task
    comment_service.rbac.enforce_permission.side_effect = AccessDeniedError
    comment_in = CommentCreate(text="А я тут мимо проходил")

    # Пользователь без прав (не автор, не исполнитель, не админ) пытается оставить коммент
    with pytest.raises(AccessDeniedError):
        await comment_service.add_comment(task_id=1, user=mock_user_stranger, comment_in=comment_in)

    mock_uow.comments.create_comment.assert_not_called()


async def test_add_comment_task_not_found(comment_service, mock_uow, mock_user_author):
    # Задачи не существует
    mock_uow.tasks.get_by_id.return_value = None
    comment_in = CommentCreate(text="Коммент в пустоту")

    with pytest.raises(TaskDoesNotExistError):
        await comment_service.add_comment(task_id=999, user=mock_user_author, comment_in=comment_in)


async def test_permissions_as_executor_and_manager(
    comment_service, mock_uow, mock_user_stranger, sample_task, sample_comment
):
    """
    Пробиваем short-circuit логику в проверке прав:
    (executor_id == user.id) or is_manager_or_admin
    """
    # === Сценарий 1: Запрос от Исполнителя ===
    sample_task.executor_id = mock_user_stranger.id
    mock_uow.tasks.get_task_by_id.return_value = sample_task
    mock_uow.comments.create_comment.return_value = sample_comment

    # Оставляем коммент как исполнитель
    await comment_service.add_comment(
        task_id=1,
        user=mock_user_stranger,
        comment_in=CommentCreate(text="Коммент исполнителя"),
    )

    # === Сценарий 2: Запрос от Менеджера (не автор и не исполнитель) ===
    sample_task.executor_id = None
    mock_user_stranger.role.name = RoleName.MANAGER

    # Оставляем коммент как менеджер
    await comment_service.add_comment(
        task_id=1,
        user=mock_user_stranger,
        comment_in=CommentCreate(text="Коммент менеджера"),
    )


async def test_get_task_comments_success(comment_service, mock_uow, sample_task, sample_comment, mock_user_author):
    mock_uow.tasks.get_by_id.return_value = sample_task
    mock_uow.comments.get_comments_by_task_id.return_value = ([sample_comment], 1)
    sample_task.executor_id = mock_user_author.id

    params = PaginationParams(page=1, size=20)

    page_result = await comment_service.get_task_comments(
        task_id=sample_task.id,
        user=mock_user_author,
        params=params,
    )

    assert page_result.items == [sample_comment]
    mock_uow.comments.get_comments_by_task_id.assert_awaited_once_with(
        task_id=sample_task.id,
        offset=params.offset,
        limit=params.limit,
    )


@pytest.mark.parametrize("is_task, exc", [(True, AccessDeniedError), (False, TaskDoesNotExistError)])
async def test_get_task_comments_with_exc(comment_service, mock_uow, sample_task, mock_user_stranger, is_task, exc):
    if is_task:
        mock_uow.tasks.get_by_id.return_value = sample_task
        comment_service.rbac.enforce_permission.side_effect = AccessDeniedError
    else:
        mock_uow.tasks.get_by_id.return_value = None

    sample_task.author_id = 111
    sample_task.executor_id = 222

    mock_user_stranger.id = 999
    mock_user_stranger.role.name = RoleName.USER
    params = PaginationParams(page=1, size=20)

    with pytest.raises(exc):
        await comment_service.get_task_comments(task_id=sample_task.id, user=mock_user_stranger, params=params)

    mock_uow.comments.get_comments_by_task_id.assert_not_awaited()
