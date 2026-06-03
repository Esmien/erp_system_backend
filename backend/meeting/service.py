from loguru import logger

from backend.core.uow import IUnitOfWork

from backend.core.constants import BusinessElementName, Action
from backend.exceptions import MeetingOverlapError, MeetingDoesNotExistsError
from backend.meeting.schemas import (
    MeetingCreate,
    MeetingCreateDTO,
    MeetingReadWithParticipants,
    MeetingUpdate,
    MeetingUpdateDTO,
)
from backend.rbac.schemas import AccessContextDTO
from backend.rbac.service import RbacService
from backend.user.schemas import UserDTO


class MeetingService:
    def __init__(self, uow: IUnitOfWork, rbac_service: RbacService):
        self.uow = uow
        self.rbac = rbac_service

    async def _get_meeting_by_id(self, meeting_id: int) -> MeetingReadWithParticipants:
        meeting = await self.uow.meetings.get_meeting_info(meeting_id=meeting_id)
        if not meeting:
            raise MeetingDoesNotExistsError("Встреча не найдена")

        return meeting

    async def create_meeting(
        self, meeting_in: MeetingCreate, author: UserDTO
    ) -> MeetingReadWithParticipants:
        """
        Создает новую встречу с проверкой накладок по времени.
        """
        async with self.uow:
            # Проверка прав на создание встреч
            await self.rbac.enforce_permission(
                user=author,
                business_element_name=BusinessElementName.MEETINGS,
                action=Action.CREATE,
                error_msg="Недостаточно прав для создания встречи",
            )

            # Проверяем накладки по времени
            overlapping_users = await self.uow.meetings.get_overlapping_participants(
                participant_ids=meeting_in.participant_ids,
                starts_on=meeting_in.datetime_start,
                ends_on=meeting_in.datetime_end,
            )

            # 3. Если есть конфликты, отменяем создание
            if overlapping_users:
                logger.info(
                    f"Конфликт времени у пользователей с ID: {overlapping_users}"
                )
                raise MeetingOverlapError(
                    f"Участники с ID {overlapping_users} заняты в это время."
                )

            # Формируем полную DTO для сохранения (добавляем автора)
            new_meeting_dto = MeetingCreateDTO(
                **meeting_in.model_dump(), author_id=author.id
            )

            # 5. Сохраняем в БД
            new_meeting = await self.uow.meetings.create_meeting(
                meeting_in=new_meeting_dto
            )

            await self.uow.commit()

        logger.success(
            f"Встреча '{new_meeting.theme}' успешно создана пользователем {author.email}"
        )
        return new_meeting

    async def get_meeting_with_participants(
        self, meeting_id: int, user: UserDTO
    ) -> MeetingReadWithParticipants:
        async with self.uow:
            meeting = await self._get_meeting_by_id(meeting_id=meeting_id)

            is_author = meeting.author_id == user.id
            is_participant = any(p.id == user.id for p in meeting.participants)

            context = AccessContextDTO(
                is_author=is_author, is_participant=is_participant
            )
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.MEETINGS,
                action=Action.READ,
                context=context,
                error_msg="Данная встреча для вас недоступна",
            )

            return meeting

    async def update_meeting(
        self, meeting_id, update_data: MeetingUpdate, user: UserDTO
    ) -> MeetingReadWithParticipants:
        update_dict = update_data.model_dump(exclude_unset=True)
        async with self.uow:
            meeting = await self._get_meeting_by_id(meeting_id=meeting_id)

            if not update_dict:
                return meeting

            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.MEETINGS,
                action=Action.UPDATE,
                context=AccessContextDTO(is_author=(user.id == meeting.author_id)),
                error_msg="Данные встречи может обновить только автор или руководитель",
            )

            update_dto = MeetingUpdateDTO(**update_dict)
            updated_meeting = await self.uow.meetings.update_meeting(
                meeting_id=meeting_id, data_for_update=update_dto
            )

            if not updated_meeting:
                raise MeetingDoesNotExistsError("Встреча не найдена")

            await self.uow.commit()

            return updated_meeting
