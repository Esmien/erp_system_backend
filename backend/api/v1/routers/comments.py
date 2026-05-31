from fastapi import status, APIRouter, Depends

from backend.api.dependencies.permissions import CurrentUserDepends, get_current_user
from backend.api.dependencies.comments import CommentCreateBody, CommentServiceDepends
from backend.comment.schemas import CommentRead
from backend.core.utils.error_schemas import ErrorResponseSchema

router = APIRouter(
    prefix="/tasks/{task_id}/comments",
    tags=["Комментарии"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    path="/",
    response_model=list[CommentRead],
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
):
    """
    Возвращает все комментарии к выбранной задаче.

    Если задача не найдена - 404 Not Found
    Если нет прав для просмотра - 403 Forbidden
    """
    return await service.get_task_comments(task_id=task_id, user=user)


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

    Если задача не найдена - 404 Not Found
    Если нет прав (не автор, не исполнитель и не руководитель) - 403 Forbidden
    """
    new_comment = await service.add_comment(
        task_id=task_id, user=user, comment_in=comment_in
    )
    return new_comment
