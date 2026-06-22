from pydantic import BaseModel

from backend.meeting.schemas import MeetingReadWithParticipants
from backend.task.schemas import TaskRead


class CalendarResponse(BaseModel):
    tasks: list[TaskRead]
    meetings: list[MeetingReadWithParticipants]


class DateRange(BaseModel):
    day: int | None = None
    month: int
    year: int
