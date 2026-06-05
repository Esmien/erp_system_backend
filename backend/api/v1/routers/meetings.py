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


@router.get(
    path="/",
    response_model=list[MeetingReadWithParticipants],
    status_code=status.HTTP_200_OK,
    summary="Получить все доступные встречи",
)
async def get_all_available_meetings(
    service: MeetingServiceDepends,
    current_user: CurrentUserDepends,
):
    """
    Получает все доступные встречи
    """
    return await service.get_all_meetings(user=current_user)


@router.get(
    path="/{meeting_id}/",
    response_model=MeetingReadWithParticipants,
    status_code=status.HTTP_200_OK,
    summary="Получить данные встречи",
    responses={
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для получения деталей встречи",
        },
        404: {"model": ErrorResponseSchema, "description": "Встреча не найдена"},
    },
)
async def get_meeting_details(
    meeting_id: int,
    service: MeetingServiceDepends,
    current_user: CurrentUserDepends,
):
    """
    Получает детали встречи
    """
    return await service.get_meeting_with_participants(
        meeting_id=meeting_id, user=current_user
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
        409: {
            "model": ErrorResponseSchema,
            "description": "Некоторые пользователи заняты в это время",
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
            "description": "Недостаточно прав для обновления встречи",
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


@router.delete(
    path="/{meeting_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить встречу",
    responses={
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для удаления встречи",
        },
        404: {"model": ErrorResponseSchema, "description": "Встреча не найдена"},
    },
)
async def delete_meeting(
    meeting_id: int,
    service: MeetingServiceDepends,
    current_user: CurrentUserDepends,
):
    """
    Удаляет встречу
    """
    await service.delete_meeting(meeting_id=meeting_id, user=current_user)
