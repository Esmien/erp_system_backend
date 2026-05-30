from fastapi import status, APIRouter, Depends

from backend.api.dependencies.permissions import CurrentUserDepends, get_current_user
from backend.api.dependencies.comments import CommentCreateBody, CommentServiceDepends
from backend.comment.schemas import CommentRead

router = APIRouter(
    prefix="/tasks/{task_id}/comments",
    tags=["Комментарии"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    path="/",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить комментарий к задаче",
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
