from fastapi import APIRouter, Depends, status

from backend.api.dependencies.calendar import (
    CalendarServiceDepends,
    YearQuery,
    MonthQuery,
    DayQuery,
)
from backend.api.dependencies.pagination import PaginationParamsDepends
from backend.api.dependencies.permissions import get_current_user, CurrentUserDepends
from backend.calendar.schemas import CalendarResponse

router = APIRouter(
    prefix="/calendar",
    tags=["Календарь"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    path="/",
    response_model=CalendarResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить задачи и встречи на выбранный период",
)
async def get_calendar(
    service: CalendarServiceDepends,
    current_user: CurrentUserDepends,
    year: YearQuery,
    month: MonthQuery,
    params: PaginationParamsDepends,
    day: DayQuery | None = None,
):
    """
    Возвращает агрегированный список задач с дедлайнами и встреч пользователя.
    Если `day` не передан, возвращает данные за весь месяц.
    """
    return await service.get_user_calendar(
        user=current_user, year=year, month=month, day=day, params=params
    )
