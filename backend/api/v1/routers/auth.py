from fastapi import APIRouter, HTTPException, status
from loguru import logger

from backend.api.dependencies.permissions import CurrentUserDepends
from backend.api.dependencies.reg_and_auth import (
    AuthFormDepends,
    AuthServiceDepends,
    RegisterServiceDepends,
)

from backend.user.schemas import UserRead, Token, UserRegister, UserChangeStatus
from backend.core.utils.error_schemas import ErrorResponseSchema
from backend.exceptions import (
    UserExistsError,
    RoleDoesNotExistsError,
    InvalidPasswordError,
    UserDoesNotExistsError,
    UserNotActiveError,
    UserAlreadyActiveError,
)


router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post(
    path="/register/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
    responses={
        400: {
            "model": ErrorResponseSchema,
            "description": "Пользователь уже существует",
        },
        503: {
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
    Пользователь существует и активен - 400 Bad Request
    Роль user не найдена - 503, ошибка на стороне сервера
    """

    # Прогоняем пайплайн регистрации пользователя:
    # проверка на существование->проверка наличия роли user в БД->присвоение роли и регистрация
    try:
        new_user = await service.register_user(user_in=user_in)
    except UserExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RoleDoesNotExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    return new_user


@router.patch(
    path="/restore/",
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
    Пользователь уже активен - 409 Conflict
    Неправильные креды - 401 Unauthorized
    """

    # Проверка на корректность кредов и активность.
    # Если креды в порядке и пользователь неактивен, то активируем
    try:
        user = await service.check_users_creds(form_data.username, form_data.password)
        await service.activate_user(user=user)
    except UserAlreadyActiveError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (UserDoesNotExistsError, InvalidPasswordError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль"
        )

    logger.info(f"Пользователь {user.name} восстановлен")
    return UserChangeStatus(
        message=f"Пользователь {user.name} успешно восстановлен",
        user=UserRead.model_validate(user),
    )


@router.post(
    path="/login/",
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
    Неправильные креды - 401 Unauthorized
    Пользователь есть, но неактивен - 403 Forbidden
    """
    # Проверяем креды, получаем JWT-токен
    try:
        user = await service.check_users_creds(form_data.username, form_data.password)
        token = service.get_auth_token(user=user)
    # Если что-то не в порядке - сообщаем в респонсе
    except (UserDoesNotExistsError, InvalidPasswordError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль"
        )
    except UserNotActiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт удален или деактивирован",
        )

    return token


@router.post(
    path="/logout/",
    status_code=status.HTTP_200_OK,
    summary="Выход из системы",
)
async def logout(current_user: CurrentUserDepends):
    """
    Выход пользователя из системы
    Примечание: мы используем JWT, поэтому здесь ничего не делаем
    """

    return {"message": "Вы успешно вышли из системы"}
