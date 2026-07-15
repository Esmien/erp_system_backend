from fastapi import APIRouter, Depends, status

from backend.api.dependencies.pagination import Page, PaginationParamsDepends
from backend.comment.api.comments_dependencies import CommentCreateBody, CommentServiceDepends
from backend.comment.schemas import CommentRead
from backend.core.utils.error_schemas import ErrorResponseSchema
from backend.rbac.api.permissions_dependencies import CurrentUserDepends, get_current_user

router = APIRouter(
    prefix="/tasks/{task_id}/comments",
    tags=["Комментарии"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    path="/",
    response_model=Page[CommentRead],
    summary="Получить список комментариев к задаче",
    responses={
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для просмотра комментариев",
        },
        404: {"model": ErrorResponseSchema, "description": "Задача не найдена"},
    },
)
async def get_comments(
    task_id: int,
    service: CommentServiceDepends,
    user: CurrentUserDepends,
    params: PaginationParamsDepends,
):
    """
    Возвращает все комментарии к выбранной задаче.
    """
    return await service.get_task_comments(task_id=task_id, user=user, params=params)


@router.post(
    path="/",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить комментарий к задаче",
    responses={
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для комментирования задачи",
        },
        404: {"model": ErrorResponseSchema, "description": "Задача не найдена"},
    },
)
async def add_comment(
    task_id: int,
    comment_in: CommentCreateBody,
    service: CommentServiceDepends,
    user: CurrentUserDepends,
):
    """
    Добавляет комментарий к задаче.
    """
    new_comment = await service.add_comment(task_id=task_id, user=user, comment_in=comment_in)
    return new_comment
