from pydantic import BaseModel

from backend.task.schemas import TaskRead
from backend.meeting.schemas import MeetingReadWithParticipants


class CalendarResponse(BaseModel):
    tasks: list[TaskRead]
    meetings: list[MeetingReadWithParticipants]


class DateRange(BaseModel):
    day: int | None = None
    month: int
    year: int
