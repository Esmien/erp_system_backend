from datetime import datetime
from typing import Annotated

from fastapi import Depends, Query

from backend.api.dependencies.uow import UowDepends
from backend.calendar.service import CalendarService


def get_calendar_service(uow: UowDepends) -> CalendarService:
    """Провайдер сервиса для работы с командами для инъекции в Annotated"""
    return CalendarService(uow=uow)


# Готовые DI для использования в роутерах
CalendarServiceDepends = Annotated[CalendarService, Depends(get_calendar_service)]
YearQuery = Annotated[
    int, Query(default_factory=lambda: datetime.now().year, ge=2026, description="Год")
]
MonthQuery = Annotated[int, Query(ge=1, le=12, description="Номер месяца")]
DayQuery = Annotated[int, Query(ge=1, le=31, description="День месяца (опционально)")]
