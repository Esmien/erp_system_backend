from backend.core.constants import BusinessElementName
from backend.core.policies import AccessLevel
from backend.core.uow import IUnitOfWork
from backend.rbac.schemas import AccessContextDTO


class RbacService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def check_permission(
        self,
        role_id: int,
        business_element_name: BusinessElementName,
        action: str,  # Например: "create", "read", "update"
        context: AccessContextDTO | None = None,
    ) -> bool:
        """
        Универсальный метод проверки прав через JSONB-политики.
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
