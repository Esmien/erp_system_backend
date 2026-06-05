from datetime import datetime

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.meeting.models import Meeting, meeting_participants
from backend.meeting.schemas import (
    MeetingCreateDTO,
    MeetingReadWithParticipants,
    MeetingUpdateDTO,
)
from backend.user.models import User


class MeetingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_meeting_by_id(self, meeting_id: int) -> Meeting | None:
        """
        Вспомогательный метод получения встречи

        Args:
            meeting_id - ID искомой встречи

        Returns:
            ORM-модель встречи или None, если не найдена
        """
        stmt = (
            select(Meeting)
            .where(Meeting.id == meeting_id)
            .options(selectinload(Meeting.participants))
        )
        meeting = (await self.session.execute(statement=stmt)).scalar_one_or_none()
        return meeting

    async def get_overlapping_participants(
        self, participant_ids: list[int], starts_on: datetime, ends_on: datetime
    ) -> list[int]:
        """
        Проверяет, есть ли у переданных пользователей встречи,
        которые пересекаются с заданным временным интервалом.

        Args:
            participant_ids - список ID участников для проверки
            starts_on - время начала встречи
            ends_on - время окончания встречи

        Returns:
            Пустой список, если пересечиний нет или список ID участников,
            у которых время занято другими встречами
        """
        if not participant_ids:
            return []

        # Собираем запрос на фильтрацию по времени занятости участников
        stmt = (
            select(meeting_participants.c.user_id)
            .join(Meeting, Meeting.id == meeting_participants.c.meeting_id)
            .where(
                # Сама фильтрация
                and_(
                    # Отсекаем всех, кто не приглашен
                    meeting_participants.c.user_id.in_(participant_ids),
                    # Проверяем, что встречи не пересекаются
                    Meeting.datetime_start < ends_on,
                    Meeting.datetime_end > starts_on,
                )
            )
            # Дедуплицируем айдишники, если у участника несколько конфликтующих встреч
            .distinct()
        )

        result = await self.session.execute(statement=stmt)
        return list(result.scalars().all())

    async def create_meeting(
        self, meeting_in: MeetingCreateDTO
    ) -> MeetingReadWithParticipants:
        """
        СОздает новую встречу

        Args:
            Модель встречи, полученная от клиента

        Returns:
            Готовая модель встречи со списком участников
        """
        # Отделяем параметры самой встречи и список участников, чтобы не получить ошибок алхимии
        meeting_data = meeting_in.model_dump(exclude={"participant_ids"})
        participant_ids = meeting_in.participant_ids

        # Собираем ORM-модель встречи без участников
        new_meeting = Meeting(**meeting_data)

        # Если участники есть — достаем их и присваиваем весь список разом
        if participant_ids:
            stmt = select(User).where(User.id.in_(participant_ids))
            result = await self.session.execute(statement=stmt)
            # Явно приводим к list, чтобы IDE понимала, что это список
            new_meeting.participants = list(result.scalars().all())
        else:
            # Если участников нет — присваиваем пустой список,
            # чтобы заглушить lazy load при валидации Pydantic
            new_meeting.participants = []

        self.session.add(new_meeting)
        await self.session.flush()

        return MeetingReadWithParticipants.model_validate(obj=new_meeting)

    async def get_meetings(
        self, user_id: int | None = None
    ) -> list[MeetingReadWithParticipants]:
        """
        Получает доступные пользователю встречи

        Args:
            user_id - ID пользователя для фильтрации встреч. Если None - возвращаем ВСЕ встречи

        Returns:
            Список встреч со списко участников
        """
        # Базовый запрос с подгрузкой участников
        stmt = select(Meeting).options(selectinload(Meeting.participants))

        if user_id:
            # Фильтр: либо автор, либо есть в списке участников
            stmt = stmt.where(
                or_(
                    Meeting.author_id == user_id,
                    Meeting.participants.any(User.id == user_id),
                )
            )

        # Сортируем по дате начала (свежие сверху)
        stmt = stmt.order_by(Meeting.datetime_start.desc())

        result = await self.session.execute(statement=stmt)
        meetings = result.scalars().all()

        # Собираем встречи в список и возвращаем
        return [MeetingReadWithParticipants.model_validate(obj=m) for m in meetings]

    async def get_meeting_info(
        self, meeting_id: int
    ) -> MeetingReadWithParticipants | None:
        """
        Возвращает полную информацию по встрече

        Args:
            meeting_id - ID встречи для чтения

        Returns:
            Данные встречи со списком участников или None, если встреча не существует
        """
        meeting = await self._get_meeting_by_id(meeting_id=meeting_id)

        return (
            MeetingReadWithParticipants.model_validate(obj=meeting) if meeting else None
        )

    async def update_meeting(
        self, meeting_id: int, data_for_update: MeetingUpdateDTO
    ) -> MeetingReadWithParticipants | None:
        """
        Обновлет данные встречи. Все поля опциональны

        Args:
            meeting_id - ID встречи для изменения
            data_for_update - данные для обновления в формате DTO

        Returns:
            Встреча с обновленными данными или None, если такой встречи не существует
        """
        meeting = await self._get_meeting_by_id(meeting_id=meeting_id)
        if not meeting:
            return None

        # Сериализуем DTO для удобной работы с данными
        update_dict = data_for_update.model_dump(exclude_unset=True)
        # Отрезаем айдишники участников
        participant_ids = update_dict.pop("participant_ids", None)

        # Обновляем данные
        for key, value in update_dict.items():
            setattr(meeting, key, value)

        if participant_ids is not None:
            # Очищаем текущий список
            meeting.participants.clear()

            # Добавлем новых участников
            if participant_ids:
                stmt = select(User).where(User.id.in_(participant_ids))
                result = await self.session.execute(stmt)
                new_participants = result.scalars().all()
                meeting.participants.extend(new_participants)

        self.session.add(instance=meeting)
        await self.session.flush()

        return MeetingReadWithParticipants.model_validate(obj=meeting)

    async def delete_meeting(self, meeting_id: int) -> None:
        """
        Удаляет встречу по ID

        Args:
            meeting_id - ID встречи для удаления
        """
        meeting = await self._get_meeting_by_id(meeting_id=meeting_id)
        if not meeting:
            return

        await self.session.delete(instance=meeting)
        await self.session.flush()

    async def get_meetings_by_date_range(
        self, user_id: int, start_dt: datetime, end_dt: datetime
    ) -> list[MeetingReadWithParticipants]:
        """
        Получает встречи за указанный период

        Args:
            user_id - ID пользователя, который запрашивает встречи
            start_dt - начало периода
            end_dt - конец периода

        Returns:
            Список отфильтрованных встреч
        """
        stmt = (
            select(Meeting)
            # Подтягиваем участников
            .options(selectinload(Meeting.participants))
            .where(
                and_(
                    # Проверяем причастность пользователя к задачам
                    or_(
                        Meeting.author_id == user_id,
                        Meeting.participants.any(User.id == user_id),
                    ),
                    # Фильтруем по датам
                    Meeting.datetime_start >= start_dt,
                    Meeting.datetime_start <= end_dt,
                )
            )
            # Сортируем - новые сверху
            .order_by(Meeting.datetime_start.asc())
        )

        result = await self.session.execute(statement=stmt)

        return [
            MeetingReadWithParticipants.model_validate(obj=m)
            for m in result.scalars().all()
        ]
