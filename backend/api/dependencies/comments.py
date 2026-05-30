from typing import Annotated

from fastapi import Body, Depends

from backend.api.dependencies.uow import UowDepends
from backend.comment.service import CommentService
from backend.comment.schemas import CommentCreate, CommentUpdate


def get_comment_service(uow: UowDepends) -> CommentService:
    """
    Провайдер сервиса задач для инъекции в Annotated.
    """
    return CommentService(uow=uow)


CommentServiceDepends = Annotated[CommentService, Depends(get_comment_service)]
CommentCreateBody = Annotated[CommentCreate, Body()]
CommentUpdateBody = Annotated[CommentUpdate, Body()]
