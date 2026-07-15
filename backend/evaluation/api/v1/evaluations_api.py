from fastapi import APIRouter, Depends, status

from backend.core.utils.error_schemas import ErrorResponseSchema
from backend.evaluation.api.evaluations_dependencies import (
    EvaluationCreateBody,
    EvaluationServiceDepends,
)
from backend.evaluation.schemas import EvaluationRead
from backend.rbac.api.permissions_dependencies import CurrentUserDepends, get_current_user

router = APIRouter(
    prefix="/tasks/{task_id}/evaluation",
    tags=["Оценка работы"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    path="/",
    response_model=EvaluationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Оценить выполнение задачи",
    responses={
        400: {"model": ErrorResponseSchema, "description": "Задача уже оценена"},
        403: {"model": ErrorResponseSchema, "description": "Недостаточно прав"},
        404: {"model": ErrorResponseSchema, "description": "Задача не найдена"},
    },
)
async def evaluate_task(
    task_id: int,
    evaluation_in: EvaluationCreateBody,
    user: CurrentUserDepends,
    service: EvaluationServiceDepends,
):
    """
    Выставляет оценку (от 1 до 5) за задачу
    Только для руководителей и администраторов

    Если оценка уже стоит - 400 Bad Request
    Если нет прав - 403 Forbidden
    Если задача не существует - 404 Not Found
    """
    evaluation = await service.evaluate_task(task_id=task_id, evaluation_in=evaluation_in, user=user)
    return evaluation


@router.get(
    path="/",
    response_model=EvaluationRead | None,
    status_code=status.HTTP_200_OK,
    summary="Получить оценку за задачу",
    responses={
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав (не участник)",
        },
        404: {"model": ErrorResponseSchema, "description": "Задача не найдена"},
    },
)
async def get_evaluation(
    task_id: int,
    user: CurrentUserDepends,
    service: EvaluationServiceDepends,
):
    """
    Возвращает оценку задачи.
    Доступно руководителям и участникам задачи (автору/исполнителю).

    Если нет прав - 403 Forbidden
    Если задача не найдена - 404 Not Found
    """
    evaluation = await service.get_evaluation(task_id=task_id, user=user)
    return evaluation
