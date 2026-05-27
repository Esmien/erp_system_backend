from fastapi import APIRouter, HTTPException, status, Depends

from backend.api.dependencies.permissions import CurrentUserDepends, get_current_user
from backend.api.dependencies.tasks import (
    TaskServiceDepends,
    TaskCreateBody,
    TaskUpdateBody,
    TaskChangeStatusBody,
    TaskStatusFilterQuery,
    TaskScopeFilterQuery,
    CommentCreateBody,
)
from backend.exceptions import (
    TaskDoesNotExistsError,
    AccessDeniedError,
    UserDoesNotExistsError,
    TeamDoesNotExistsError,
)
from backend.task.schemas import TaskRead, CommentRead

router = APIRouter(
    prefix="/tasks", tags=["Задачи"], dependencies=[Depends(get_current_user)]
)


@router.get(
    path="/{task_id}/",
    response_model=TaskRead,
    status_code=status.HTTP_200_OK,
    summary="Получить информацию о задаче",
)
async def get_task(task_id: int, service: TaskServiceDepends):
    """
    Возвращает данные задачи.
    Если задача не существует - 404 Not Found
    """
    try:
        task = await service.get_task(task_id=task_id)
        return task  # pragma: no cover
    except TaskDoesNotExistsError as e:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    path="/",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать задачу",
)
async def create_task(
    service: TaskServiceDepends, task_in: TaskCreateBody, author: CurrentUserDepends
):
    """
    Создает задачу
    """
    task = await service.create_task(task_in=task_in, author=author)
    return task  # pragma: no cover


@router.patch(
    path="/{task_id}/",
    response_model=TaskRead,
    status_code=status.HTTP_200_OK,
    summary="Обновить задачу",
)
async def update_task(
    task_id: int,
    service: TaskServiceDepends,
    update_data: TaskUpdateBody,
    user: CurrentUserDepends,
):
    """
    Обновляет задачу.

    Если задачи не существует - 404 Not Found
    Если нет доступа (не руководитель или автор) - 403 Forbidden
    Попытка назначить исполнителем несуществующего пользователя - 400 Bad Request
    """
    try:
        updated_task = await service.update_task(
            task_id=task_id, update_data=update_data, user=user
        )
        return updated_task
    except TaskDoesNotExistsError as e:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except UserDoesNotExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.patch(
    path="/{task_id}/status/",
    response_model=TaskRead,
    status_code=status.HTTP_200_OK,
    summary="Обновить статус задачи",
)
async def change_status(
    task_id: int,
    service: TaskServiceDepends,
    new_status: TaskChangeStatusBody,
    user: CurrentUserDepends,
):
    """
    Обновляет статус задачи

    Если задача не найдена - 404 Not Found
    Если нет прав (необходимо быть руководителем или автором/исполнителем) - 403 Forbidden
    """
    try:
        updated_task = await service.change_status(
            task_id=task_id, new_status=new_status, user=user
        )
        return updated_task
    except TaskDoesNotExistsError as e:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.delete(
    path="/{task_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить задачу",
)
async def delete_task(
    task_id: int, service: TaskServiceDepends, user: CurrentUserDepends
):
    """
    Полностью удаляет задачу

    Если задача не существует - 404 Not Found
    Если нет доступа (не руководитель или автор) - 403 Forbidden
    """
    try:
        await service.delete_task(task_id=task_id, user=user)
    except TaskDoesNotExistsError as e:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.get(
    path="/",
    response_model=list[TaskRead],
    status_code=status.HTTP_200_OK,
    summary="Получить список задач по фильтрам",
)
async def get_tasks_by_filter(
    service: TaskServiceDepends,
    user: CurrentUserDepends,
    task_status: TaskStatusFilterQuery | None = None,
    scope: TaskScopeFilterQuery = "my",
):
    """
    Возвращает список задач с учетом фильтров.

    Если нет доступа - 403 Forbidden
    """
    try:
        return await service.get_filtered_tasks(
            user=user, scope=scope, task_status=task_status
        )
    except AccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except TeamDoesNotExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    path="/{task_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить комментарий к задаче",
)
async def add_comment(
    task_id: int,
    comment_in: CommentCreateBody,
    service: TaskServiceDepends,
    user: CurrentUserDepends,
):
    """
    Добавляет комментарий к задаче.

    Если задача не найдена - 404 Not Found
    Если нет прав (не автор, не исполнитель и не руководитель) - 403 Forbidden
    """
    try:
        new_comment = await service.add_comment(
            task_id=task_id, user=user, comment_in=comment_in
        )
        return new_comment
    except TaskDoesNotExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
