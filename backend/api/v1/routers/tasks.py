from fastapi import APIRouter, HTTPException, status, Depends

from backend.api.dependencies.permissions import CurrentUserDepends, get_current_user
from backend.api.dependencies.tasks import (
    TaskServiceDepends,
    TaskCreateBody,
    TaskUpdateBody,
    TaskChangeStatusBody,
)
from backend.exceptions import (
    TaskDoesNotExistsError,
    AccessDeniedError,
    UserDoesNotExistsError,
)
from backend.task.schemas import TaskRead


router = APIRouter(
    prefix="/tasks", tags=["Задачи"], dependencies=[Depends(get_current_user)]
)


@router.get(
    path="/",
    response_model=list[TaskRead],
    status_code=status.HTTP_200_OK,
    summary="Получить все задачи",
)
async def get_all_tasks(service: TaskServiceDepends):
    return await service.get_all_tasks()


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
    Если нет доступа (не руководитель или автор) - 403 Forbidden
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


@router.patch(
    path="/{task_id}/status",
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
    Если нет доступа (не руководитель или автор) - 403 Forbidden
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
