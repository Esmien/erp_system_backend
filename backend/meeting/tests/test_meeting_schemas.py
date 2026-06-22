from datetime import UTC, datetime, timedelta

import pytest

from backend.exceptions import DatetimeMismatchError
from backend.meeting.schemas import MeetingCreate, MeetingUpdate


def test_meeting_create_valid_dates():
    """Успешное создание схемы с валидными датами"""
    now = datetime.now(UTC)
    start = now + timedelta(hours=1)
    end = start + timedelta(hours=1)

    meeting = MeetingCreate(
        theme="Тестовая встреча",
        datetime_start=start,
        datetime_end=end,
        participant_ids=[1, 2, 3],
    )
    assert meeting.theme == "Тестовая встреча"
    assert len(meeting.participant_ids) == 3


@pytest.mark.parametrize(
    "start, end, exc_msg",
    [
        (
            datetime.now(UTC) - timedelta(hours=1),
            datetime.now(UTC) + timedelta(hours=1),
            "Встреча не может начаться раньше текущего времени",
        ),
        (
            datetime.now(UTC) + timedelta(hours=2),
            datetime.now(UTC) + timedelta(hours=1),
            "Встреча не может окончиться раньше или одновременно с началом",
        ),
    ],
)
def test_meeting_create_invalid_dates(start, end, exc_msg):
    with pytest.raises(DatetimeMismatchError, match=exc_msg):
        MeetingCreate(theme="Тестовая встреча", datetime_start=start, datetime_end=end)


def test_meeting_update_partial():
    """Успешная валидация частичного обновления"""
    # Обновляем только тему
    update_data = MeetingUpdate(theme="Новая тема")
    assert update_data.theme == "Новая тема"
    assert update_data.datetime_start is None
    assert update_data.participant_ids is None
