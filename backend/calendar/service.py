import calendar
from datetime import date, datetime, time, timezone

from backend.api.dependencies.pagination import PaginationParams, Page
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
        params: PaginationParams,
        day: int | None = None,
    ) -> CalendarResponse:
        """
        Собирает DTO со списками встреч и задач за выбранные даты

        Args:
            user - позьзователь, который запрашивает данные
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
            # Получаем кортежи (items, total) из обновленных репозиториев
            tasks_items, tasks_total = await self.uow.tasks.get_tasks_by_date_range(
                offset=params.offset,
                limit=params.limit,
                user_id=user.id,
                start_date=start_date,
                end_date=end_date,
            )
            (
                meetings_items,
                meetings_total,
            ) = await self.uow.meetings.get_meetings_by_date_range(
                offset=params.offset,
                limit=params.limit,
                user_id=user.id,
                start_dt=start_dt,
                end_dt=end_dt,
            )

        # Заворачиваем каждый список в отдельную страницу
        tasks_page = Page.create(items=tasks_items, total=tasks_total, params=params)
        meetings_page = Page.create(
            items=meetings_items, total=meetings_total, params=params
        )

        # Отдаем в общую DTO календаря
        return CalendarResponse(tasks=tasks_page, meetings=meetings_page)
