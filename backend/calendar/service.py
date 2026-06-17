import calendar
from datetime import date, datetime, time, timezone

from backend.core.uow import IUnitOfWork
from backend.calendar.schemas import CalendarResponse
from backend.user.schemas import UserDTO


class CalendarService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def get_user_calendar(
        self,
        user: UserDTO,
        year: int,
        month: int,
        day: int | None = None,
    ) -> CalendarResponse:
        """
        Собирает DTO со списками встреч и задач за выбранные даты

        Args:
            user - пользователь, который запрашивает данные
            year - год, за который нужны данные
            month - месяц, за который нужны данные
            day - день, за который нужны данные

        Returns:
            DTO со всеми встречами и задачами пользователя
        """

        # Вычисляем границы для типа date (для Задач)
        if day:
            start_date = date(year, month, day)
            end_date = start_date
        else:
            _, last_day = calendar.monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day)

        # Вычисляем границы для типа datetime с UTC (для Встреч)
        start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)

        async with self.uow:
            # Получаем встречи и задачи
            tasks_items = await self.uow.tasks.get_tasks_by_date_range(
                user_id=user.id,
                start_date=start_date,
                end_date=end_date,
            )
            meetings_items = await self.uow.meetings.get_meetings_by_date_range(
                user_id=user.id,
                start_date=start_dt,
                end_date=end_dt,
            )

        return CalendarResponse(tasks=tasks_items, meetings=meetings_items)
