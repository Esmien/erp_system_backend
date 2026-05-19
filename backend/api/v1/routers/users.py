from fastapi import APIRouter, status

from backend.api.dependencies.users import (
    CurrentUserDepends,
    UserServiceDepends,
    UserUpdateBody,
)
from backend.core.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get(
    path="/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Получить инфо о себе",
)
async def get_my_info(current_user: CurrentUserDepends):
    return current_user


@router.patch(
    path="/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Обновить данные профиля",
)
async def update_my_info(
    update_data: UserUpdateBody,
    current_user: CurrentUserDepends,
    service: UserServiceDepends,
):
    """
    Обновляет личные данные пользователя.
    Можно передать только те поля, которые нужно изменить (например, только name).
    """
    updated_user = await service.update_profile(
        user=current_user, update_data=update_data
    )
    return updated_user
