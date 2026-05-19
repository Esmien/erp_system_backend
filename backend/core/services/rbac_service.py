from backend.core.database.repository.rbac import RbacRepository


class RbacService:
    def __init__(self, repo: RbacRepository):
        self.repo = repo

    async def check_permission(
        self, role_id: int, element_name: str, permission: str
    ) -> bool:
        rule = await self.repo.get_access_rule(role_id, element_name)

        if not rule:
            return False

        return getattr(rule, permission, False)
