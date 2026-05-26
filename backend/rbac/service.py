from loguru import logger

from backend.core.uow import IUnitOfWork
from backend.rbac.repository import RbacRepository


class RbacService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def check_permission(
        self, role_id: int, element_name: str, permission: str
    ) -> bool:
        """
        Проверяет права доступа к ресурсу для роли

        Args:
            role_id - проверяемая роль
            element_name - ресурс, к которому проверяется доступ
            permission - правило доступа к ресурсу

        Returns:
            True - если доступ разрешен, иначе False
        """
        async with self.uow:
            rule = await self.uow.rbac.get_access_rule(role_id, element_name)

        if not rule:
            logger.info(f"Не найдено правило доступа к {element_name} для роли ID {role_id}.")
            return False

        # Если передано несуществующее правило
        if not hasattr(rule, permission):
            logger.warning(f"Неизвестный permission: {permission}")
            return False

        return getattr(rule, permission, False)
