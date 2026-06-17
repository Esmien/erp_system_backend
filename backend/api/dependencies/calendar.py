from typing import Annotated

from fastapi import Depends

from backend.api.dependencies.uow import UowDepends
from backend.calendar.schemas import DateRange
from backend.calendar.service import CalendarService


def get_calendar_service(uow: UowDepends) -> CalendarService:
    """
    Провайдер сервиса календаря для инъекции в Annotated.
    """
    return CalendarService(uow=uow)


CalendarServiceDepends = Annotated[CalendarService, Depends(get_calendar_service)]
DateRangeDepends = Annotated[DateRange, Depends()]
