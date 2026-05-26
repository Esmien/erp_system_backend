from fastapi import APIRouter, status

from backend.api.dependencies.permissions import CurrentUserDepends
from backend.api.dependencies.users import (
    UserServiceDepends,
    UserUpdateBody,
)
from backend.user.schemas import UserRead

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get(
    path="/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Получить инфо о себе",
)
async def get_my_info(current_user: CurrentUserDepends):
    """
    Возвращает информацию о пользователе
    """
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


@router.delete(
    path="/me",
    status_code=status.HTTP_200_OK,
    summary="'Мягкое' удаление текущего пользователя",
)
async def delete_me(
    current_user: CurrentUserDepends,
    service: UserServiceDepends,
):
    """
    'Мягкое' удаление пользователя (is_active=False)
    Аккаунт восстановить можно через /auth/restore
    """

    # Удаляем пользователя, делая его неактивным
    await service.soft_delete_profile(user=current_user)
    return {"message": f"Пользователь {current_user.name} удален"}
