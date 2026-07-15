from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.user.models import Role, User
from backend.user.schemas import RoleForCodeDTO, UserDTO


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_user_for_update(self, user_id: int | None = None, tg_id: int | None = None) -> User | None:
        """
        Вспомогательный метод для получения модели пользователя из БД

        Args:
            user_id - ID искомого пользователя

        Returns:
            Найденная модель или None, если пользователя с таким ID не существует
        """
        stmt = select(User)

        if user_id:
            stmt = stmt.where(User.id == user_id)

        if tg_id:
            stmt = stmt.where(User.tg_id == tg_id)

        stmt = stmt.with_for_update()
        result = await self.session.execute(statement=stmt)
        return result.scalar_one_or_none()

    async def get_all_roles(self) -> list[RoleForCodeDTO] | None:
        """
        Получает список всех ролей, доступных в БД

        Returns:
            Список полученных ролей
        """
        stmt = select(Role.name)
        result = await self.session.execute(statement=stmt)
        raw_roles = result.scalars().all()

        return [RoleForCodeDTO(name=role.value if hasattr(role, "value") else role) for role in raw_roles]

    async def update_user(
        self, update_dict: dict[str, Any], user_id: int | None = None, tg_id: int | None = None
    ) -> UserDTO | None:
        """
        Обновляет данные пользователя (имя, фамилия, отчество, TelegramID)

        Args:
            user_id - ID пользователя для обновления. Опциональный
            tg_id - TelegramID пользователя для обновления. Опциональный
            update_dict - данные для обновления

        Returns:
            Обновленная модель пользователя или None, если пользователь не найден
        """
        id_for_update = {}

        if user_id:
            id_for_update = {"user_id": user_id}

        if tg_id:
            id_for_update = {"tg_id": tg_id}

        user_model = await self._get_user_for_update(**id_for_update)

        if not user_model:
            return None

        # Модифицируем модель обновленными данными
        for key, value in update_dict.items():
            setattr(user_model, key, value)

        self.session.add(instance=user_model)
        await self.session.flush()

        return UserDTO.model_validate(obj=user_model)

    async def soft_delete_user(self, user_id: int) -> UserDTO | None:
        """
        Выполняет мягкое удаление пользователя (деактивацию)

        Args:
            user_id - ID пользователя для деактивации
        """
        user_model = await self._get_user_for_update(user_id=user_id)

        if not user_model:
            return None

        user_model.is_active = False
        self.session.add(instance=user_model)
        await self.session.flush()

        return UserDTO.model_validate(obj=user_model)
