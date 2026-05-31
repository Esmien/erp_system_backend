from fastapi import APIRouter, status, Depends

from backend.api.dependencies.permissions import CurrentUserDepends, get_current_user
from backend.api.dependencies.tasks import (
    TaskServiceDepends,
    TaskCreateBody,
    TaskUpdateBody,
    TaskChangeStatusBody,
    TaskStatusFilterQuery,
    TaskScopeFilterQuery,
)
from backend.core.utils.error_schemas import ErrorResponseSchema
from backend.task.schemas import TaskRead

router = APIRouter(
    prefix="/tasks", tags=["Задачи"], dependencies=[Depends(get_current_user)]
)


@router.get(
    path="/{task_id}/",
    response_model=TaskRead,
    status_code=status.HTTP_200_OK,
    summary="Получить информацию о задаче",
    responses={
        404: {"model": ErrorResponseSchema, "description": "Задача не найдена"},
    },
)
async def get_task(task_id: int, service: TaskServiceDepends):
    """
    Возвращает данные задачи.
    Если задача не существует - 404 Not Found
    """
    task = await service.get_task(task_id=task_id)
    return task


@router.get(
    path="/",
    response_model=list[TaskRead],
    status_code=status.HTTP_200_OK,
    summary="Получить список задач по фильтрам",
    responses={
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для просмотра задач",
        },
        404: {
            "model": ErrorResponseSchema,
            "description": "Пользователь не состоит в команде",
        },
    },
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
    Если пользователь не состоит в команде, но ищет с командой в фильтрах - 404 Not Found
    """
    return await service.get_filtered_tasks(
        user=user, scope=scope, task_status=task_status
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
    responses={
        400: {
            "model": ErrorResponseSchema,
            "description": "Попытка назначить несуществующего исполнителя",
        },
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для обновления задачи",
        },
        404: {"model": ErrorResponseSchema, "description": "Задача не найдена"},
    },
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
    updated_task = await service.update_task(
        task_id=task_id, update_data=update_data, user=user
    )
    return updated_task


@router.patch(
    path="/{task_id}/status/",
    response_model=TaskRead,
    status_code=status.HTTP_200_OK,
    summary="Обновить статус задачи",
    responses={
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для изменения статуса",
        },
        404: {"model": ErrorResponseSchema, "description": "Задача не найдена"},
    },
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
    updated_task = await service.change_status(
        task_id=task_id, new_status=new_status, user=user
    )
    return updated_task


@router.delete(
    path="/{task_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить задачу",
    responses={
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для удаления задачи",
        },
        404: {"model": ErrorResponseSchema, "description": "Задача не найдена"},
    },
)
async def delete_task(
    task_id: int, service: TaskServiceDepends, user: CurrentUserDepends
):
    """
    Полностью удаляет задачу

    Если задача не существует - 404 Not Found
    Если нет доступа (не руководитель или автор) - 403 Forbidden
    """
    await service.delete_task(task_id=task_id, user=user)
