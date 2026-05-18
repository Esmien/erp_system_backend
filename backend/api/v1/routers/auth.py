from fastapi import APIRouter, HTTPException, status, Depends
from loguru import logger

from backend.api.deps import (
    get_current_user,
    AuthFormDepends,
    AuthServiceDepends,
    RegisterServiceDepends,
)
from backend.core.database.models.users import User
from backend.core.schemas.user import UserRead, Token, UserRegister, UserChangeStatus
from backend.core.schemas.error_schemas import ErrorResponseSchema
from backend.exceptions import (
    UserExistsError,
    RoleDoesNotExistsError,
    InvalidPasswordError,
    UserDoesNotExistsError,
)


router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
    responses={
        400: {
            "model": ErrorResponseSchema,
            "description": "Пользователь уже существует",
        },
        404: {
            "model": ErrorResponseSchema,
            "description": "Роль не найдена",
        },
    },
)
async def register_user(
    user_in: UserRegister,
    service: RegisterServiceDepends,
):
    """
    Регистрирует пользователя, назначая ему по умолчанию роль "user"
    """

    try:
        new_user = await service.register_user(user_in=user_in)
    except UserExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован!",
        )
    except RoleDoesNotExistsError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запрашиваемая роль не найдена",
        )

    return new_user


@router.patch(
    "/restore",
    response_model=UserChangeStatus,
    status_code=status.HTTP_200_OK,
    summary="Восстановление пользователя",
)
async def restore_user(
    form_data: AuthFormDepends,
    service: AuthServiceDepends,
):
    """
    Восстанавливает активность пользователя после 'мягкого' удаления

    Args:
        form_data - данные пользователя для восстановления
        repo - репозиторий для работы с аутентификацией

    Raises:
        HTTPException: Если пользователь не найден (404), уже активен (409) или неверный пароль (401)

    Returns:
        UserChangeStatus: Восстановленный пользователь и сообщение об успешном восстановлении
    """

    try:
        user = await service.check_users_creds(form_data.username, form_data.password)
        await service.activate_user(user=user)
    except UserDoesNotExistsError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь с таким email не зарегистрирован",
        )
    except UserExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Пользователь уже активен"
        )
    except InvalidPasswordError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль"
        )

    logger.info(f"Пользователь {user.name} восстановлен")
    return UserChangeStatus(
        message=f"Пользователь {user.name} успешно восстановлен", user=user
    )


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Вход в систему",
)
async def login(
    form_data: AuthFormDepends,
    service: AuthServiceDepends,
):
    """
    Аутентификация пользователя

    Args:
        form_data - данные пользователя для аутентификации
        service - Сессия БД

    Raises:
        HTTPException: Если пользователь не найден или не активен (404), неверный лог/пасс (401)

    Returns:
        Token: Токен доступа
    """
    try:
        user = await service.check_users_creds(form_data.username, form_data.password)
        token = await service.get_auth_token(user=user)
    except UserDoesNotExistsError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не зарегистрирован",
        )
    except InvalidPasswordError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль"
        )

    return token


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Выход из системы",
)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Выход пользователя из системы
    Примечание: мы используем JWT, поэтому здесь ничего не делаем

    Args:
        current_user (User): Текущий пользователь

    Returns:
        Сообщение об успешном выходе
    """

    return {"message": "Вы успешно вышли из системы"}
