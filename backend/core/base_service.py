from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any
from pydantic import BaseModel

from backend.core.base_repository import BaseRepository
from backend.core.uow import IUnitOfWork
from backend.core.enums import Action, BusinessElementName
from backend.rbac.schemas import AccessContextDTO
from backend.rbac.service import RbacService
from backend.user.schemas import UserDTO

DTOType = TypeVar("DTOType", bound=BaseModel)


class BaseService(ABC, Generic[DTOType]):
    def __init__(self, uow: IUnitOfWork, rbac_service: RbacService):
        self.uow = uow
        self.rbac = rbac_service

    # --- Абстрактные свойства ---

    @property
    @abstractmethod
    def repository(self) -> BaseRepository[Any, DTOType]: ...

    @property
    @abstractmethod
    def business_element(self) -> BusinessElementName: ...

    @property
    @abstractmethod
    def not_found_exception(self) -> Exception: ...

    def build_abac_context(self, obj: DTOType, user: UserDTO) -> AccessContextDTO:
        return AccessContextDTO(is_author=False, is_participant=False)

    # --- Внутренние хелперы ---

    async def get_or_raise(self, obj_id: int) -> DTOType:
        obj = await self.repository.get_by_id(obj_id=obj_id)
        if not obj:
            raise self.not_found_exception
        return obj

    async def check_permissions(
        self,
        user: UserDTO,
        action: Action,
        obj: DTOType | None = None,
        error_msg: str = "Недостаточно прав для этого действия",
    ) -> None:
        context = self.build_abac_context(obj=obj, user=user) if obj else None

        await self.rbac.enforce_permission(
            user=user,
            business_element_name=self.business_element,
            action=action,
            context=context,
            error_msg=error_msg,
        )

    # --- Универсальный CRUD ---

    async def get(self, obj_id: int, user: UserDTO) -> DTOType:
        """Получение записи по ID с проверкой прав на чтение"""
        async with self.uow:
            obj = await self.get_or_raise(obj_id=obj_id)
            await self.check_permissions(user=user, action=Action.READ, obj=obj)
            return obj

    async def create(self, create_data: dict[str, Any], user: UserDTO) -> DTOType:
        """Стандартное создание записи с проверкой прав"""
        async with self.uow:
            await self.check_permissions(user=user, action=Action.CREATE)
            obj = await self.repository.create(**create_data)
            await self.uow.commit()
            return obj

    async def update(
        self, obj_id: int, update_data: dict[str, Any], user: UserDTO
    ) -> DTOType:
        """Универсальное обновление"""
        async with self.uow:
            obj = await self.get_or_raise(obj_id=obj_id)
            await self.check_permissions(user=user, action=Action.UPDATE, obj=obj)

            updated_obj = await self.repository.update(
                obj_id=obj_id, update_data=update_data
            )
            if not updated_obj:
                raise self.not_found_exception

            await self.uow.commit()
            return updated_obj

    async def delete(self, obj_id: int, user: UserDTO) -> None:
        """Универсальное удаление"""
        async with self.uow:
            obj = await self.get_or_raise(obj_id=obj_id)
            await self.check_permissions(user=user, action=Action.DELETE, obj=obj)

            await self.repository.delete(obj_id=obj_id)
            await self.uow.commit()
