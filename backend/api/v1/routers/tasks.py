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
    prefix="/tasks",
    tags=["Задачи"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    path="/{task_id}/",
    response_model=TaskRead,
    status_code=status.HTTP_200_OK,
    summary="Получить информацию о задаче",
    responses={
        403: {"model": ErrorResponseSchema, "description": "Нет прав на просмотр"},
        404: {"model": ErrorResponseSchema, "description": "Задача не найдена"},
    },
)
async def get_task(
    task_id: int,
    service: TaskServiceDepends,
    current_user: CurrentUserDepends,
):
    """
    Возвращает данные задачи с проверкой прав на чтение
    """
    task = await service.get(obj_id=task_id, user=current_user)
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
    current_user: CurrentUserDepends,
    task_status: TaskStatusFilterQuery | None = None,
    scope: TaskScopeFilterQuery = "my",
):
    """
    Возвращает список задач с учетом фильтров
    """
    return await service.get_filtered_tasks(
        user=current_user, scope=scope, task_status=task_status
    )


@router.post(
    path="/",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать задачу",
    responses={
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для создания задачи",
        },
    },
)
async def create_task(
    service: TaskServiceDepends,
    task_in: TaskCreateBody,
    current_user: CurrentUserDepends,
):
    """
    Создает задачу
    """
    return await service.create_task(task_in=task_in, author=current_user)


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
    current_user: CurrentUserDepends,
):
    """
    Обновляет задачу (только руководитель или автор)
    """
    updated_task = await service.update_task(
        task_id=task_id, update_data=update_data, user=current_user
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
    current_user: CurrentUserDepends,
):
    """
    Обновляет статус задачи (исполнитель, автор или руководитель)
    """
    updated_task = await service.change_status(
        task_id=task_id, new_status=new_status, user=current_user
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
    task_id: int,
    service: TaskServiceDepends,
    current_user: CurrentUserDepends,
):
    """
    Полностью удаляет задачу
    """
    await service.delete(obj_id=task_id, user=current_user)
