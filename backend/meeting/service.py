from loguru import logger

from backend.api.dependencies.pagination import Page, PaginationParams
from backend.core.base_service import BaseService
from backend.core.enums import AccessLevel, Action, BusinessElementName
from backend.exceptions import (
    MeetingDoesNotExistError,
    MeetingOverlapError,
    UnknownAccessLevelError,
)
from backend.meeting.repository import MeetingRepository
from backend.meeting.schemas import (
    MeetingCreate,
    MeetingCreateDTO,
    MeetingReadWithParticipants,
    MeetingUpdate,
    MeetingUpdateDTO,
)
from backend.rbac.schemas import AccessContextDTO
from backend.user.schemas import UserDTO


class MeetingService(BaseService[MeetingReadWithParticipants]):
    @property
    def repository(self) -> MeetingRepository:
        return self.uow.meetings

    @property
    def business_element(self) -> BusinessElementName:
        return BusinessElementName.MEETINGS

    @property
    def not_found_exception(self) -> Exception:
        return MeetingDoesNotExistError("Встреча не найдена")

    def build_abac_context(self, obj: MeetingReadWithParticipants, user: UserDTO) -> AccessContextDTO:
        is_participant = any(p.id == user.id for p in obj.participants)
        return AccessContextDTO(
            is_author=obj.author_id == user.id,
            is_participant=is_participant or (obj.author_id == user.id),
        )

    async def create_meeting(self, meeting_in: MeetingCreate, author: UserDTO) -> MeetingReadWithParticipants:
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
            await self.check_permissions(
                user=author,
                action=Action.CREATE,
                error_msg="Вы не можете создать встречу",
            )

            # Проверяем накладки по времени
            if meeting_in.participant_ids:
                ids_to_check = list(set(meeting_in.participant_ids + [author.id]))

                overlapping_users = await self.uow.meetings.get_overlapping_participants(
                    participant_ids=ids_to_check,
                    starts_on=meeting_in.datetime_start,
                    ends_on=meeting_in.datetime_end,
                )

                # Если есть конфликты, отменяем создание
                if overlapping_users:
                    logger.info(f"Конфликт времени у пользователей с ID: {overlapping_users}")
                    raise MeetingOverlapError(f"Участники с ID {overlapping_users} заняты в это время.")

            # Формируем полную DTO для сохранения (добавляем автора)
            new_meeting_dto = MeetingCreateDTO(**meeting_in.model_dump(), author_id=author.id)

            # Сохраняем в БД
            new_meeting = await self.repository.create_meeting(meeting_in=new_meeting_dto)

            await self.uow.commit()

        logger.info(f"Встреча '{new_meeting.theme}' успешно создана пользователем {author.email}")
        return new_meeting

    async def get_all_meetings(self, user: UserDTO, params: PaginationParams) -> Page[MeetingReadWithParticipants]:
        """
        Получает все доступные пользователю встречи

        Args:
            user - запрашивающий встречи пользователь
            params - параметры пагинации

        Returns:
            Объект страницы (Page), содержащий список комментариев и метаданные пагинации

        Raises:
            UnknownAccessLevelError - если уровень доступа не описан в политиках, проблема сервера
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

            # Пагинируем
            meetings, total = await self.uow.meetings.get_meetings(
                offset=params.offset, limit=params.limit, user_id=filter_user_id
            )

            return Page.create(items=meetings, total=total, params=params)

    async def get_meeting_with_participants(self, meeting_id: int, user: UserDTO) -> MeetingReadWithParticipants:
        """
        Получает встречу со списком участников

        Args:
            meeting_id - ID встречи
            user - запрашивающий данные встречи пользователь

        Returns:
            Данные встречи со всеми участниками

        Raises:
            MeetingDoesNotExistsError - если встреча не нашлась по ID
        """
        async with self.uow:
            meeting = await self.get_or_raise(obj_id=meeting_id)
            if not meeting:
                raise self.not_found_exception

            await self.check_permissions(
                user=user,
                action=Action.READ,
                error_msg="Вы не можете получить данные этой встречи",
            )

            return meeting

    async def update_meeting(
        self, meeting_id: int, update_data: MeetingUpdate, user: UserDTO
    ) -> MeetingReadWithParticipants:
        """
        Обновляет данные встречи

        Args:
            meeting_id - ID обновляемой встречи
            update_data - данные для обновления в формате DTO
            user - пользователь, который обновляет встречу

        Returns:
            Обновленная встреча

        Raises:
            MeetingDoesNotExistsError - если встреча не нашлась
        """
        # Сериализуем DTO для удобной работы
        update_dict = update_data.model_dump(exclude_unset=True)

        async with self.uow:
            meeting = await self.get_or_raise(obj_id=meeting_id)

            # Если данных для обновления нет, просто возвращаем исходную встречу
            if not update_dict:
                return meeting

            # Проверяем права на обновление
            await self.check_permissions(
                user=user,
                action=Action.UPDATE,
                obj=meeting,
                error_msg="Данные встречи может обновить только автор или руководитель",
            )

            # Собираем DTO для передачи в репозиторий
            update_dto = MeetingUpdateDTO(**update_dict)
            # Обновляем встречу
            updated_meeting = await self.repository.update_meeting(meeting_id=meeting_id, data_for_update=update_dto)

            # Если на стороне репо что-то пошло не так, сообщаем, что встреча  не найдена
            if not updated_meeting:
                raise self.not_found_exception

            await self.uow.commit()

            return updated_meeting
