from fastapi import APIRouter, Depends, status

from backend.api.dependencies.evaluations import EvaluationServiceDepends
from backend.api.dependencies.permissions import CurrentUserDepends, get_current_user
from backend.api.dependencies.users import (
    UserServiceDepends,
    UserUpdateBody,
)
from backend.core.utils.error_schemas import ErrorResponseSchema
from backend.evaluation.schemas import UserStatisticsRead
from backend.user.schemas import UserRead

router = APIRouter(
    prefix="/users",
    tags=["Пользователи"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    path="/me/",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Получить инфо о себе",
)
async def get_my_info(current_user: CurrentUserDepends):
    """
    Возвращает информацию о пользователе
    """
    return current_user


@router.get(
    path="/me/statistics/",
    response_model=UserStatisticsRead,
    status_code=status.HTTP_200_OK,
    summary="Получить свою статистику оценок",
)
async def get_my_statistics(
    current_user: CurrentUserDepends,
    service: EvaluationServiceDepends,
):
    """
    Возвращает среднюю оценку и количество оцененных задач для текущего пользователя.
    """
    return await service.get_my_statistics(user=current_user)


@router.patch(
    path="/me/",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Обновить данные профиля",
    responses={
        400: {
            "model": ErrorResponseSchema,
            "description": "Пользователь не существует",
        },
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для обновления профиля",
        },
    },
)
async def update_my_info(
    update_data: UserUpdateBody,
    current_user: CurrentUserDepends,
    service: UserServiceDepends,
):
    """
    Обновляет личные данные пользователя
    Можно передать только те поля, которые нужно изменить (например, только name)
    """
    updated_user = await service.update_profile(user=current_user, update_data=update_data)
    return updated_user


@router.delete(
    path="/me/",
    status_code=status.HTTP_200_OK,
    summary="'Мягкое' удаление текущего пользователя",
    responses={
        400: {
            "model": ErrorResponseSchema,
            "description": "Пользователь не существует",
        },
        403: {
            "model": ErrorResponseSchema,
            "description": "Недостаточно прав для удаления профиля",
        },
    },
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
