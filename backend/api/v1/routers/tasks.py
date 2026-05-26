from fastapi import APIRouter, HTTPException, status

from backend.api.dependencies.permissions import CurrentUserDepends
from backend.api.dependencies.tasks import (
    TaskServiceDepends,
    TaskCreateBody,
    TaskUpdateBody,
)
from backend.exceptions import (
    TaskDoesNotExistsError,
    AccessDeniedError,
    UserDoesNotExistsError,
)
from backend.task.schemas import TaskRead

router = APIRouter(prefix="/tasks", tags=["Задачи"])


@router.get(
    path="/{task_id}",
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
    except TaskDoesNotExistsError:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена",
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
    path="/{task_id}",
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
    Если нет доступа - 403 Forbidden
    Попытка назначить исполнителем несуществующего пользователя - 400 Bad Request
    """
    try:
        updated_task = await service.update_task(
            task_id=task_id, update_data=update_data, user=user
        )
        return updated_task
    except TaskDoesNotExistsError:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена",
        )
    except AccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except UserDoesNotExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Попытка назначить несуществующего исполнителя",
        )


@router.delete(
    path="/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить задачу",
)
async def delete_task(
    task_id: int, service: TaskServiceDepends, user: CurrentUserDepends
):
    """
    Полностью удаляет задачу

    Если задача не существует - 404 Not Found
    Если нет доступа - 403 Forbidden
    """
    try:
        await service.delete_task(task_id=task_id, user=user)
    except TaskDoesNotExistsError:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена",
        )
    except AccessDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
