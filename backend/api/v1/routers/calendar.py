from fastapi import APIRouter, Depends, status

from backend.api.dependencies.calendar import CalendarServiceDepends, DateRangeDepends
from backend.api.dependencies.permissions import CurrentUserDepends, get_current_user
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
    date_range: DateRangeDepends,
):
    """
    Возвращает агрегированный список задач с дедлайнами и встреч пользователя.
    Если `day` не передан, возвращает данные за весь месяц.
    """
    return await service.get_user_calendar(
        user=current_user,
        year=date_range.year,
        month=date_range.month,
        day=date_range.day,
    )
