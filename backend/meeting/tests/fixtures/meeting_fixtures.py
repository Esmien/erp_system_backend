from datetime import datetime, timedelta

import pytest

from backend.meeting.repository import MeetingRepository
from backend.meeting.schemas import MeetingCreate, MeetingReadWithParticipants
from backend.meeting.service import MeetingService
from backend.user.schemas import UserDTO, RoleDTO


@pytest.fixture
def meeting_service(mock_uow, mock_rbac_service):
    return MeetingService(uow=mock_uow, rbac_service=mock_rbac_service)


@pytest.fixture
def meeting_repo(db_session):
    return MeetingRepository(session=db_session)


@pytest.fixture
def mock_user_for_meeting():
    return UserDTO(
        id=1,
        email="test@test.com",
        name="Test",
        hashed_password="hash",
        is_active=True,
        role_id=1,
        role=RoleDTO(id=1, name="user"),
    )


@pytest.fixture
def meeting_in():
    return MeetingCreate(
        theme="Синхронизация бэкенда",
        datetime_start=datetime.now(),
        datetime_end=datetime.now() + timedelta(hours=1),
        participant_ids=[2, 3],
    )


@pytest.fixture
def expected_meeting(mock_user_for_meeting, meeting_in):
    return MeetingReadWithParticipants(
        id=1,
        author_id=mock_user_for_meeting.id,
        theme=meeting_in.theme,
        datetime_start=meeting_in.datetime_start,
        datetime_end=meeting_in.datetime_end,
        participants=[],
    )
