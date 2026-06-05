from datetime import datetime, timedelta
from unittest.mock import ANY

import pytest

from backend.core.constants import AccessLevel
from backend.exceptions import (
    MeetingOverlapError,
    MeetingDoesNotExistsError,
    AccessDeniedError,
)
from backend.meeting.schemas import (
    MeetingCreate,
    MeetingUpdate,
)


@pytest.mark.asyncio
class TestMeetingService:
    async def test_create_meeting_success(
        self,
        meeting_service,
        mock_uow,
        mock_user_for_meeting,
        meeting_in,
        expected_meeting,
    ):
        # Настраиваем моки
        mock_uow.meetings.get_overlapping_participants.return_value = []
        mock_uow.meetings.create_meeting.return_value = expected_meeting

        # Вызов
        result = await meeting_service.create_meeting(meeting_in, mock_user_for_meeting)

        # Проверки
        assert result.id == expected_meeting.id
        mock_uow.meetings.get_overlapping_participants.assert_called_once()
        mock_uow.meetings.create_meeting.assert_called_once()
        mock_uow.commit.assert_called_once()

    async def test_create_meeting_with_overlap(
        self, meeting_service, mock_uow, mock_user_for_meeting
    ):
        meeting_in = MeetingCreate(
            theme="Синхронизация бэкенда",
            datetime_start=datetime.now(),
            datetime_end=datetime.now() + timedelta(hours=1),
            participant_ids=[2, 3],
        )

        # Имитируем, что у пользователя с ID 2 уже есть встреча
        mock_uow.meetings.get_overlapping_participants.return_value = [2]

        with pytest.raises(MeetingOverlapError) as exc_info:
            await meeting_service.create_meeting(meeting_in, mock_user_for_meeting)

        assert "заняты в это время" in str(exc_info.value)
        mock_uow.meetings.create_meeting.assert_not_called()
        mock_uow.commit.assert_not_called()

    # --- Новые тесты для get_all_meetings ---

    async def test_get_all_meetings_all_access(
        self, meeting_service, mock_uow, mock_user_for_meeting, mock_rbac_service
    ):
        # Имитируем, что RBAC дал полный доступ (ALL)
        mock_rbac_service.get_list_access_level.return_value = AccessLevel.ALL
        mock_uow.meetings.get_meetings.return_value = []

        await meeting_service.get_all_meetings(mock_user_for_meeting)

        mock_rbac_service.get_list_access_level.assert_called_once()
        # При ALL фильтр по юзеру отключается
        mock_uow.meetings.get_meetings.assert_called_once_with(user_id=None)

    async def test_get_all_meetings_participant_access(
        self, meeting_service, mock_uow, mock_user_for_meeting, mock_rbac_service
    ):
        # Имитируем, что RBAC дал доступ только причастным (PARTICIPANT)
        mock_rbac_service.get_list_access_level.return_value = AccessLevel.PARTICIPANT
        mock_uow.meetings.get_meetings.return_value = []

        await meeting_service.get_all_meetings(mock_user_for_meeting)

        mock_rbac_service.get_list_access_level.assert_called_once()
        # При PARTICIPANT должен передаваться ID пользователя для фильтрации
        mock_uow.meetings.get_meetings.assert_called_once_with(
            user_id=mock_user_for_meeting.id
        )

    async def test_get_all_meetings_access_denied(
        self, meeting_service, mock_uow, mock_user_for_meeting, mock_rbac_service
    ):
        # Имитируем ситуацию, когда RBAC выбрасывает ошибку прав доступа
        mock_rbac_service.get_list_access_level.side_effect = AccessDeniedError(
            "У вас нет прав для просмотра встреч"
        )

        with pytest.raises(AccessDeniedError):
            await meeting_service.get_all_meetings(mock_user_for_meeting)

        # Убеждаемся, что до БД запрос даже не дошел
        mock_uow.meetings.get_meetings.assert_not_called()

    async def test_update_meeting_success(
        self, meeting_service, mock_uow, mock_user_for_meeting, expected_meeting
    ):
        meeting_id = 1
        update_data = MeetingUpdate(theme="Новая тема встречи")

        expected_meeting.id = meeting_id

        mock_uow.meetings.get_meeting_info.return_value = expected_meeting
        mock_uow.meetings.update_meeting.return_value = expected_meeting

        await meeting_service.update_meeting(
            meeting_id, update_data, mock_user_for_meeting
        )

        mock_uow.meetings.update_meeting.assert_called_once_with(
            meeting_id=meeting_id, data_for_update=ANY
        )
        mock_uow.commit.assert_called_once()

    async def test_delete_meeting_not_found(
        self, meeting_service, mock_uow, mock_user_for_meeting
    ):
        mock_uow.meetings.get_meeting_info.return_value = None

        with pytest.raises(MeetingDoesNotExistsError):
            await meeting_service.delete_meeting(999, mock_user_for_meeting)
