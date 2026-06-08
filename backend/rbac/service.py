from backend.core.enums import BusinessElementName, Action
from backend.core.policies import AccessLevel
from backend.core.uow import IUnitOfWork
from backend.exceptions import AccessDeniedError
from backend.rbac.schemas import AccessContextDTO
from backend.user.schemas import UserDTO


class RbacService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def get_list_access_level(
        self,
        user: UserDTO,
        business_element_name: BusinessElementName,
        action: Action,
        error_msg: str = "У вас нет прав для просмотра этого списка",
    ) -> AccessLevel:
        """
        Используется для получения списков (коллекций).
        Проверяет наличие базовых прав и возвращает уровень доступа для фильтрации в БД.

        Args:
            user - пользователь для проверки прав
            business_element_name - название сущности, к которой требуется доступ
            action - какое действие нужно совершить (CRUD)
            error_msg - сообщение об ошибке для передачи наверх внутри исключения

        Returns:
            Уровень доступа пользователя по отношению к бизнес-сущности

        Raises:
            AccessDeniedError - если прав у пользователя недостаточно
        """
        # Получаем правило из БД
        rule = await self.uow.rbac.get_access_rule(
            role_id=user.role_id, business_element_name=business_element_name
        )

        # Правило не нашлось или политики для роли пустые
        if not rule or not rule.policies:
            raise AccessDeniedError(error_msg)

        # Вытаскиваем из политик уровень доступа для нужного действия
        access_level = rule.policies.get(action)

        # Если для нужного действия нет прав у пользователя
        if not access_level:
            raise AccessDeniedError(error_msg)

        return AccessLevel(access_level)

    async def check_permission(
        self,
        role_id: int,
        business_element_name: BusinessElementName,
        action: str,
        context: AccessContextDTO | None = None,
    ) -> bool:
        """
        Универсальный метод проверки прав доступа к объекту через JSONB-политики.

        Args:
            role_id - роль пользователя для проверки
            business_element_name - бизнес-сущность, к которой требуется доступ
            action - CRUD-действие, на которое запрашиваются права
            context - дополнительные параметры проверки, если базовых недостаточно

        Returns:
            True, если доступ разрешен или False, если нет
        """
        context = context or AccessContextDTO()

        rule = await self.uow.rbac.get_access_rule(
            role_id=role_id, business_element_name=business_element_name
        )

        if not rule or not rule.policies:
            return False

        required_access = rule.policies.get(action)
        if not required_access:
            return False

        # Политика разрешает действие всем
        if required_access == AccessLevel.ALL:
            return True

        # Политика требует причастности к ресурсу
        if required_access == AccessLevel.PARTICIPANT:
            return context.is_participant

        # Политика требует быть создателем ресурсу
        if required_access == AccessLevel.AUTHOR:
            return context.is_author

        return False

    async def enforce_permission(
        self,
        user: UserDTO,
        business_element_name: BusinessElementName,
        action: str,
        context: AccessContextDTO | None = None,
        error_msg: str = "Недостаточно прав для выполнения операции",
    ) -> None:
        """
        Обертка над check_permission.
        Сразу выбрасывает исключение, если прав нет.

        Args:
            user - проверяемый пользователь
            business_element_name - название бизнес-сущности к которой нужен доступ
            action - CRUD-действие
            context - дополнительный контекст, если базовых правил недостаточно (проверка на причастность)
            error_msg - сообщение, которое будет передано в сообщении исключения

        Raises:
            AccessDeniedError - если доступа нет
        """
        has_access = await self.check_permission(
            role_id=user.role_id,
            business_element_name=business_element_name,
            action=action,
            context=context,
        )

        if not has_access:
            raise AccessDeniedError(error_msg)
