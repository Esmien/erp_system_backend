from typing import Annotated, Literal

from fastapi import Depends, Body, Query

from backend.api.dependencies.rbac import RbacServiceDepends
from backend.api.dependencies.uow import UowDepends
from backend.core.constants import TaskStatus
from backend.task.schemas import TaskCreate, TaskUpdate, TaskChangeStatus
from backend.task.service import TaskService


def get_task_service(uow: UowDepends, rbac: RbacServiceDepends) -> TaskService:
    """
    Провайдер сервиса задач для инъекции в Annotated.
    """
    return TaskService(uow=uow, rbac_service=rbac)


# Готовые DI для использования в роутерах
TaskServiceDepends = Annotated[TaskService, Depends(get_task_service)]

TaskCreateBody = Annotated[TaskCreate, Body()]
TaskUpdateBody = Annotated[TaskUpdate, Body()]
TaskChangeStatusBody = Annotated[TaskChangeStatus, Body()]
TaskStatusFilterQuery = Annotated[
    TaskStatus, Query(description="Фильтр по статусу задачи")
]
TaskScopeFilterQuery = Annotated[
    Literal["my", "team", "all"],
    Query(
        description="Область видимости: my - мои задачи, team - задачи команды, all - все"
    ),
]
