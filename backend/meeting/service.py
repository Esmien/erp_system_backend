from loguru import logger

from backend.core.uow import IUnitOfWork

from backend.core.constants import BusinessElementName, Action, AccessLevel
from backend.exceptions import (
    MeetingOverlapError,
    MeetingDoesNotExistsError,
    UnknownAccessLevelError,
)
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
        """
        Вспомогательный метод для получения модели встречи

        Args:
            meeting_id - ID искомой встречи

        Returns:
            Встреча со списком участников

        Raises:
            MeetingDoesNotExistsError - если такой встречи не существует
        """
        meeting = await self.uow.meetings.get_meeting_info(meeting_id=meeting_id)
        if not meeting:
            raise MeetingDoesNotExistsError("Встреча не найдена")

        return meeting

    async def create_meeting(
        self, meeting_in: MeetingCreate, author: UserDTO
    ) -> MeetingReadWithParticipants:
        """
        Создает новую встречу с проверкой накладок по времени.

        Args:
            meeting_in - схема задачи для создания, полученная от клиента
            author - модель пользователя, который создает задачу

        Returns:
            Свежесозданная встреча со списком участников
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

            # Если есть конфликты, отменяем создание
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

            # Сохраняем в БД
            new_meeting = await self.uow.meetings.create_meeting(
                meeting_in=new_meeting_dto
            )

            await self.uow.commit()

        logger.success(
            f"Встреча '{new_meeting.theme}' успешно создана пользователем {author.email}"
        )
        return new_meeting

    async def get_all_meetings(
        self, user: UserDTO
    ) -> list[MeetingReadWithParticipants]:
        """
        Получает все доступные пользователю встречи

        Args:
            user - запрашивающий встречи пользователь
        """
        async with self.uow:
            # Проверяем глобальные права на просмотр встреч
            access_level = await self.rbac.get_list_access_level(
                user=user,
                business_element_name=BusinessElementName.MEETINGS,
                action=Action.READ,
                error_msg="У вас нет прав для просмотра встреч",
            )

            # Если нет ограничений (руководитель, например) - отдаем все встречи без привязки к личному ID
            if access_level == AccessLevel.ALL:
                filter_user_id = None
            # Если проверка вернула требование причастности, добавляем личный ID в фильтрацию
            elif access_level in (AccessLevel.PARTICIPANT, AccessLevel.AUTHOR):
                filter_user_id = user.id
            # Если же вернулись неизвестные права - проблема сервера
            else:
                raise UnknownAccessLevelError("Неизвестный уровень доступа")

            return await self.uow.meetings.get_meetings(user_id=filter_user_id)

    async def get_meeting_with_participants(
        self, meeting_id: int, user: UserDTO
    ) -> MeetingReadWithParticipants:
        """
        Получает встречу со списком участников

        Args:
            meeting_id - ID встречи
            user - запрашивающий данные встречи пользователь

        Returns:
            Данные встречи со всеми участниками
        """
        async with self.uow:
            meeting = await self._get_meeting_by_id(meeting_id=meeting_id)

            # Проверяем статус пользователя для контекста
            is_author = meeting.author_id == user.id
            is_participant = any(p.id == user.id for p in meeting.participants)

            context = AccessContextDTO(
                is_author=is_author, is_participant=is_participant
            )
            # Проверяем права доступа
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
        """
        Обновляет данные встречи

        Args:
            meeting_id - ID обновляемой встречи
            update_data - данные для обновления в формате DTO
            user - пользовател, который обновляет встречу

        Returns:
            Обновленная встреча
        """
        # Сериализуем DTO для удобной работы
        update_dict = update_data.model_dump(exclude_unset=True)

        async with self.uow:
            meeting = await self._get_meeting_by_id(meeting_id=meeting_id)

            # Если данных для обновления нет, просто возвращаем исходную встречу
            if not update_dict:
                return meeting

            # Проверяем права на обновление
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.MEETINGS,
                action=Action.UPDATE,
                context=AccessContextDTO(is_author=(user.id == meeting.author_id)),
                error_msg="Данные встречи может обновить только автор или руководитель",
            )

            # Собираем DTO для передачи в репозиторий
            update_dto = MeetingUpdateDTO(**update_dict)
            # Обновляем встречу
            updated_meeting = await self.uow.meetings.update_meeting(
                meeting_id=meeting_id, data_for_update=update_dto
            )

            # Если на стороне репо что-то пошло не так, сообщаем, что встреча  не найдена
            if not updated_meeting:
                raise MeetingDoesNotExistsError("Встреча не найдена")

            await self.uow.commit()

            return updated_meeting

    async def delete_meeting(self, meeting_id: int, user: UserDTO) -> None:
        """
        Удаляет встречу

        Args:
            meeting_id - ID встречи для удаления
            user - пользователь, который хочет удалить встречу
        """
        async with self.uow:
            meeting = await self._get_meeting_by_id(meeting_id=meeting_id)

            # Проверяем, может ли текущий пользователь удалять встречи
            await self.rbac.enforce_permission(
                user=user,
                business_element_name=BusinessElementName.MEETINGS,
                action=Action.DELETE,
                context=AccessContextDTO(is_author=user.id == meeting.author_id),
                error_msg="Недостаточно прав для удаления задачи",
            )

            await self.uow.meetings.delete_meeting(meeting_id=meeting_id)
            await self.uow.commit()
