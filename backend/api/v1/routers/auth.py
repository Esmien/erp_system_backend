from fastapi import APIRouter, Depends, status
from loguru import logger

from backend.api.dependencies.permissions import CredentialsDepends, CurrentUserDepends, get_current_user
from backend.api.dependencies.redis import RedisDepends
from backend.api.dependencies.reg_and_auth import (
    AuthServiceDepends,
    RegisterServiceDepends,
)
from backend.api.dependencies.users import UserServiceDepends
from backend.core.utils.error_schemas import ErrorResponseSchema
from backend.user.schemas import (
    RefreshTokenRequest,
    RegisterCode,
    Token,
    UserChangeStatus,
    UserLogin,
    UserRead,
    UserRegister,
)

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post(
    path="/generate-register-code/",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterCode,
    summary="Генерация кода регистрации (Только для админов)",
)
async def generate_registration_code(
    current_user: CurrentUserDepends,
    service: UserServiceDepends,
    redis: RedisDepends,
):
    # Генерируем случайную строку из 6 символов (заглавные буквы и цифры)
    new_code = await service.generate_registration_code(user=current_user, redis=redis)
    logger.info(f"Сгенерирован новый регистрационный код: {new_code}")
    return new_code


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
        500: {
            "model": ErrorResponseSchema,
            "description": "Роль не найдена",
        },
    },
)
async def register_user(
    user_in: UserRegister,
    service: RegisterServiceDepends,
    redis: RedisDepends,
):
    """
    Регистрирует пользователя, назначая ему по умолчанию роль "user"
    Пользователь существует и активен - 400 Bad Request
    Роль user не найдена - 500, ошибка на стороне сервера
    """

    # Прогоняем пайплайн регистрации пользователя:
    # проверка на существование->проверка наличия роли user в БД->присвоение роли и регистрация
    new_user = await service.register_user(user_in=user_in, redis=redis)

    return new_user


@router.patch(
    path="/restore/",
    response_model=UserChangeStatus,
    status_code=status.HTTP_200_OK,
    summary="Восстановление пользователя",
    responses={
        401: {
            "model": ErrorResponseSchema,
            "description": "Неверные данные учетной записи или пользователь не существует",
        },
        409: {"model": ErrorResponseSchema, "description": "Пользователь уже активен"},
    },
)
async def restore_user(
    credentials: UserLogin,
    service: AuthServiceDepends,
):
    """
    Восстанавливает активность пользователя после 'мягкого' удаления
    Пользователь уже активен - 409 Conflict
    Неправильные креды - 401 Unauthorized
    """

    # Проверка на корректность кредов и активность.
    # Если креды в порядке и пользователь неактивен, то активируем
    user = await service.check_users_creds(credentials.username, credentials.password)
    await service.activate_user(user=user)

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
    responses={
        401: {
            "model": ErrorResponseSchema,
            "description": "Неверные данные учетной записи или пользователь не существует",
        },
        403: {"model": ErrorResponseSchema, "description": "Пользователь не активен"},
    },
)
async def login(
    credentials: UserLogin,
    service: AuthServiceDepends,
):
    """
    Аутентификация пользователя
    Неправильные креды - 401 Unauthorized
    Пользователь есть, но неактивен - 403 Forbidden
    """
    # Проверяем креды, получаем JWT-токен
    user = await service.check_users_creds(credentials.username, credentials.password)
    tokens = service.get_auth_tokens(user=user)

    return tokens


@router.post(
    path="/refresh/",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Обновление access-токена",
    responses={
        401: {"model": ErrorResponseSchema, "description": "Невалидный токен"},
    },
)
async def refresh_access_token(
    request_data: RefreshTokenRequest,
    service: AuthServiceDepends,
    redis: RedisDepends,
):
    """Обновляет пару токенов по валидному refresh-токену"""
    return await service.refresh_tokens(refresh_token=request_data.refresh_token, redis=redis)


@router.post(
    path="/logout/",
    status_code=status.HTTP_200_OK,
    summary="Выход из системы",
    dependencies=[Depends(get_current_user)],
)
async def logout(
    credentials: CredentialsDepends,
    service: AuthServiceDepends,
    redis: RedisDepends,
):
    """
    Выход пользователя из системы
    При логауте токен добавляется в блэклист
    """
    # Вытаскиваем токен напрямую из заголовка
    await service.logout(token=credentials.credentials, redis=redis)

    return {"message": "Вы успешно вышли из системы"}
