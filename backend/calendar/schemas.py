from pydantic import BaseModel

from backend.api.dependencies.pagination import Page
from backend.task.schemas import TaskRead
from backend.meeting.schemas import MeetingReadWithParticipants


class CalendarResponse(BaseModel):
    tasks: Page[TaskRead]
    meetings: Page[MeetingReadWithParticipants]
