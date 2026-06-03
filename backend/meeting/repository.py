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
        stmt = (
            select(Meeting)
            .where(Meeting.id == meeting_id)
            .options(selectinload(Meeting.participants))
        )
        meeting = (await self.session.execute(stmt)).scalar_one_or_none()
        return meeting

    async def get_overlapping_participants(
        self, participant_ids: list[int], starts_on: datetime, ends_on: datetime
    ) -> list[int]:
        """
        Проверяет, есть ли у переданных пользователей встречи,
        которые пересекаются с заданным временным интервалом.
        """
        if not participant_ids:
            return []

        stmt = (
            select(meeting_participants.c.user_id)
            .join(Meeting, Meeting.id == meeting_participants.c.meeting_id)
            .where(
                and_(
                    meeting_participants.c.user_id.in_(participant_ids),
                    Meeting.datetime_start < ends_on,
                    Meeting.datetime_end > starts_on,
                )
            )
            .distinct()
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_meeting(
        self, meeting_in: MeetingCreateDTO
    ) -> MeetingReadWithParticipants:
        """
        Создает встречу и связывает её с участниками (Many-to-Many).
        """
        # Отделяем participant_ids, так как такого поля в БД нет
        meeting_data = meeting_in.model_dump(exclude={"participant_ids"})
        participant_ids = meeting_in.participant_ids

        # Создаем пустой объект встречи
        new_meeting = Meeting(**meeting_data)

        # Если переданы участники, достаем их инстансы из БД
        if participant_ids:
            stmt = select(User).where(User.id.in_(participant_ids))
            result = await self.session.execute(stmt)
            participants = result.scalars().all()

            # Привязываем участников к встрече
            new_meeting.participants.extend(participants)

        self.session.add(new_meeting)
        await self.session.flush()

        return MeetingReadWithParticipants.model_validate(new_meeting)

    async def get_meetings(
        self, user_id: int | None = None
    ) -> list[MeetingReadWithParticipants]:
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

        result = await self.session.execute(stmt)
        meetings = result.scalars().all()

        return [MeetingReadWithParticipants.model_validate(m) for m in meetings]

    async def get_meeting_info(
        self, meeting_id: int
    ) -> MeetingReadWithParticipants | None:
        meeting = await self._get_meeting_by_id(meeting_id=meeting_id)

        return MeetingReadWithParticipants.model_validate(meeting) if meeting else None

    async def update_meeting(
        self, meeting_id: int, data_for_update: MeetingUpdateDTO
    ) -> MeetingReadWithParticipants | None:
        meeting = await self._get_meeting_by_id(meeting_id=meeting_id)
        if not meeting:
            return None

        update_dict = data_for_update.model_dump(exclude_unset=True)
        participant_ids = update_dict.pop("participant_ids", None)

        for key, value in update_dict.items():
            setattr(meeting, key, value)

        if participant_ids is not None:
            # Очищаем текущий список
            meeting.participants.clear()

            if participant_ids:
                stmt = select(User).where(User.id.in_(participant_ids))
                result = await self.session.execute(stmt)
                new_participants = result.scalars().all()
                meeting.participants.extend(new_participants)

        self.session.add(instance=meeting)
        await self.session.flush()

        return MeetingReadWithParticipants.model_validate(obj=meeting)

    async def delete_meeting(self, meeting_id: int) -> None:
        meeting = await self._get_meeting_by_id(meeting_id=meeting_id)

        if not meeting:
            return

        await self.session.delete(meeting)
        await self.session.flush()
