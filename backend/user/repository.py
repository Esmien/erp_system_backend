from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.enums import RoleName
from backend.user.models import User, Role
from backend.user.schemas import UserDTO, UserCreateDTO


class RegisterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_user(self, user_to_register: UserCreateDTO) -> UserDTO | None:
        """
        Регистрирует пользователя после всех проверок

        Args:
            user_to_register - DTO-модель пользователя для регистрации со всеми нужными полями

        Returns:
            Модель зарегистрированного пользователя с подгруженной ролью
        """
        stmt = (
            insert(User)
            .values(**user_to_register.model_dump(exclude_none=True))
            .on_conflict_do_nothing(index_elements=[User.email])
            .returning(User.id)
        )

        # Если email уникальный, то получим ID пользователя, если нет - None
        new_user_id = await self.session.scalar(statement=stmt)

        if not new_user_id:
            return None

        # Подгружаем роль пользователя
        stmt_select = (
            select(User).where(User.id == new_user_id).options(selectinload(User.role))
        )

        result_select = await self.session.execute(stmt_select)
        user_with_role = result_select.scalar_one()

        return UserDTO.model_validate(obj=user_with_role)

    async def get_role_id(self, role_name: RoleName) -> int | None:
        """
        Получает ID роли по ее названию

        Args:
            role_name - название роли в формате StrEnum

        Returns:
            ID роли - если нашлась, None - если нет
        """
        stmt = select(Role).where(Role.name == role_name)
        result_role = await self.session.execute(statement=stmt)
        role_model = result_role.scalar_one_or_none()

        return role_model.id if role_model else None


class AuthRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_user_model_by_email(
        self, user_email: str, for_update: bool = False
    ) -> User | None:
        """
        Вспомогательный метод для получения модели пользователя

        Args:
            user_email - Email искомого пользователя
            for_update - флаг для блокировки транзакции при обновлении данных в БД

        Returns:
            Модель пользователя или None, если пользователя с таким Email нет
        """
        stmt = select(User).where(User.email == user_email)

        if for_update:
            stmt = stmt.with_for_update()

        result = await self.session.execute(statement=stmt)
        user_model = result.scalar_one_or_none()

        return user_model if user_model else None

    async def get_user_and_role_by_user_id(self, user_id: int) -> UserDTO | None:
        """
        Получает модель пользователя по ID и его роль

        Args:
            user_id - ID пользователя

        Returns:
            Модель пользователя с загруженной ролью или None, если пользователь не найден
        """
        # selectinload для подгрузки роли, так как дальше будем к ней обращаться
        stmt = select(User).where(User.id == user_id).options(selectinload(User.role))
        result = await self.session.execute(statement=stmt)
        user_model = result.scalar_one_or_none()

        return UserDTO.model_validate(obj=user_model) if user_model else None

    async def get_user(self, email: str) -> UserDTO | None:
        """
        Получает модель пользователя по email

        Args:
            email - email пользователя

        Returns:
            Модель пользователя или None, если email не найден
        """
        user = await self._get_user_model_by_email(user_email=email)

        return UserDTO.model_validate(obj=user) if user else None

    async def activate_user(self, user_email: str) -> UserDTO | None:
        """
        Активирует пользователя

        Args:
            user_email - Email существующего неактивного пользователя для активации

        Returns:
            Обновленная модель пользователя с is_active=True или None, если пользователь не существует
        """
        # Защищаем через for_update от одновременных попыток изменить статус
        user = await self._get_user_model_by_email(
            user_email=user_email, for_update=True
        )

        if not user:
            return None

        user.is_active = True
        await self.session.flush()

        return UserDTO.model_validate(obj=user)


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_user_for_update(self, user_id: int) -> User | None:
        """
        Вспомогательный метод для получения модели пользователя из БД

        Args:
            user_id - ID искомого пользователя

        Returns:
            Найденная модель или None, если пользователя с таким ID не существует
        """
        stmt = select(User).where(User.id == user_id).with_for_update()
        result = await self.session.execute(statement=stmt)
        return result.scalar_one_or_none()

    async def update_user(
        self, user_id: int, update_dict: dict[str, Any]
    ) -> UserDTO | None:
        """
        Обновляет данные пользователя (имя, фамилия, отчество)

        Args:
            user_id - ID пользователя для обновления
            update_dict - данные для обновления

        Returns:
            Обновленная модель пользователя
        """

        user_model = await self._get_user_for_update(user_id=user_id)

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
