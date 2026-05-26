from typing import Annotated

from fastapi import Depends, Body

from backend.api.dependencies.uow import UowDepends
from backend.task.schemas import TaskCreate, TaskUpdate, TaskChangeStatus
from backend.task.service import TaskService


async def get_task_service(uow: UowDepends) -> TaskService:
    """
    Провайдер сервиса задач для инъекции в Annotated.
    """
    return TaskService(uow=uow)


# Готовые DI для использования в роутерах
TaskServiceDepends = Annotated[TaskService, Depends(get_task_service)]

TaskCreateBody = Annotated[TaskCreate, Body()]
TaskUpdateBody = Annotated[TaskUpdate, Body()]
TaskChangeStatusBody = Annotated[TaskChangeStatus, Body()]
