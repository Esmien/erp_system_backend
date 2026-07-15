from loguru import logger

from backend.core.enums import Action, BusinessElementName
from backend.core.uow import IUnitOfWork
from backend.exceptions import (
    RoleDoesNotExistError,
    UserDoesNotExistError,
)
from backend.rbac.schemas import AccessContextDTO
from backend.rbac.service import RbacService
from backend.user.schemas import (
    RoleForCodeDTO,
    UserDTO,
    UserUpdate,
)


class UserService:
    def __init__(self, uow: IUnitOfWork, rbac_service: RbacService):
        self.uow = uow
        self.rbac = rbac_service

    async def get_all_roles(self, user: UserDTO) -> list[RoleForCodeDTO]:
        """
        Получает список всех доступных ролей

        Args:
            user: запрашивающий роли пользователь

        Returns:
            Список ролей
        """
        await self.rbac.enforce_permission(
            user=user,
            business_element_name=BusinessElementName.USERS,
            action=Action.CREATE,
            error_msg="Недостаточно прав для получения списка ролей",
        )

        roles = await self.uow.users.get_all_roles()

        if not roles:
            raise RoleDoesNotExistError("Роли не найдены")

        return roles

    async def update_profile(self, user: UserDTO, update_data: UserUpdate) -> UserDTO:
        """
        Обновляет данные пользователя (ФИО)

        Args:
            user - модель пользователя для обновления
            update_data - данные, которые пользователь хочет обновить

        Returns:
            Обновленная модель пользователя (или исходная, если данных для обновления нет)

        Raises:
            UserDoesNotExistsError - если репозиторий не нашел пользователя
        """

        # Сериализуем данные для дальнейшей обработки в репозитории, исключая не заданные поля
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            logger.info(f"Нет данных для обновления пользователя ID: {user.id}, Email: {user.email}.")
            return user

        # Проверка прав - обновлять профили могут либо владельцы, либо руководители
        await self.rbac.enforce_permission(
            user=user,
            business_element_name=BusinessElementName.USERS,
            action=Action.UPDATE,
            context=AccessContextDTO(is_author=True),
            error_msg="Недостаточно прав для обновления профиля",
        )

        updated_user = await self.uow.users.update_user(user_id=user.id, update_dict=update_dict)

        if not updated_user:
            logger.info(f"Не найден пользователь для обновления, ID: {user.id}, Email: {user.email}.")
            raise UserDoesNotExistError

        await self.uow.commit()

        logger.info(f"Пользователь ID: {user.id}, Email: {user.email} успешно обновлен.")
        return updated_user

    async def soft_delete_profile(self, user: UserDTO) -> None:
        """
        Мягко удаляет пользователя (деактивирует)

        Args:
            user - модель пользователя для удаления

        Raises:
            UserDoesNotExists - если пользователь не найден
        """
        # Проверка прав - удалить можно только свой профиль. Если руководитель, то любой
        await self.rbac.enforce_permission(
            user=user,
            business_element_name=BusinessElementName.USERS,
            action=Action.DELETE,
            context=AccessContextDTO(is_author=True),
            error_msg="Недостаточно прав для удаления профиля",
        )

        deactivated_user = await self.uow.users.soft_delete_user(user_id=user.id)

        if not deactivated_user:
            logger.info(f"Не найден пользователь для удаления, ID: {user.id}, Email: {user.email}.")
            raise UserDoesNotExistError

        await self.uow.commit()
        logger.info(f"Пользователь ID: {deactivated_user.id}, Email: {deactivated_user.email} успешно деактивирован.")
