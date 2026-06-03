from fastapi import APIRouter, Depends, status

from backend.api.dependencies.meetings import (
    MeetingServiceDepends,
    MeetingCreateBody,
    MeetingUpdateBody,
)
from backend.api.dependencies.permissions import get_current_user, CurrentUserDepends
from backend.core.utils.error_schemas import ErrorResponseSchema
from backend.meeting.schemas import MeetingReadWithParticipants

router = APIRouter(
    prefix="/meetings",
    tags=["Встречи"],
    dependencies=[Depends(get_current_user)],
)


@router.post(
    path="/",
    response_model=MeetingReadWithParticipants,
    status_code=status.HTTP_201_CREATED,
    summary="Создать встречу",
    responses={
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для создания встречи",
        },
    },
)
async def create_meeting(
    service: MeetingServiceDepends,
    meeting_in: MeetingCreateBody,
    current_user: CurrentUserDepends,
):
    """
    Создает новую встречу с проверкой календарей участников
    """
    return await service.create_meeting(meeting_in=meeting_in, author=current_user)


@router.patch(
    path="/{meeting_id}/",
    response_model=MeetingReadWithParticipants,
    status_code=status.HTTP_200_OK,
    summary="Обновить данные встречи",
    responses={
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для создания встречи",
        },
        404: {"model": ErrorResponseSchema, "description": "Встреча не найдена"},
    },
)
async def update_meeting(
    meeting_id: int,
    service: MeetingServiceDepends,
    meeting_update: MeetingUpdateBody,
    current_user: CurrentUserDepends,
):
    """
    Обновляет данные встречи
    """
    return await service.update_meeting(
        meeting_id=meeting_id, update_data=meeting_update, user=current_user
    )
