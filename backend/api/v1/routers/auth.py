from fastapi import APIRouter, Depends, status
from loguru import logger

from backend.api.dependencies.permissions import CredentialsDepends, get_current_user
from backend.api.dependencies.redis import RedisConfigDepends, RedisDepends
from backend.api.dependencies.reg_and_auth import (
    AuthServiceDepends,
    BotSecretHeader,
    RegisterServiceDepends,
)
from backend.core.utils.error_schemas import ErrorResponseSchema
from backend.user.schemas import (
    RefreshTokenRequest,
    Token,
    UserChangeStatus,
    UserLogin,
    UserRead,
    UserRegister,
    UserTelegramLink,
    UserTelegramLogin,
    UserTelegramUnlink,
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
        500: {
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
    Роль user не найдена - 500, ошибка на стороне сервера
    """

    # Прогоняем пайплайн регистрации пользователя:
    # проверка на существование->проверка наличия роли user в БД->присвоение роли и регистрация
    new_user = await service.register_user(user_in=user_in)

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
    token = service.get_auth_token(user=user)

    return token


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
    path="/telegram/login/",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Аутентификация через телеграм",
    responses={
        401: {
            "model": ErrorResponseSchema,
            "description": "Неверные данные учетной записи или пользователь не существует",
        },
        403: {"model": ErrorResponseSchema, "description": "Пользователь не активен"},
    },
)
async def telegram_login(
    service: AuthServiceDepends,
    credentials: UserTelegramLogin,
):
    """
    Аутентификация пользователя через телеграм-бота
    Неправильные креды - 401 Unauthorized
    Пользователь есть, но неактивен - 403 Forbidden
    """
    user = await service.authenticate_by_telegram(tg_id=credentials.tg_id)

    return service.get_auth_token(user=user)


@router.post(
    path="/telegram/link/",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Привязка Telegram ID к аккаунту",
    responses={
        401: {
            "model": ErrorResponseSchema,
            "description": "Неверные данные учетной записи или пользователь не существует",
        },
        403: {"model": ErrorResponseSchema, "description": "Пользователь не активен"},
    },
)
async def link_telegram_account(
    service: AuthServiceDepends,
    credentials: UserTelegramLink,
):
    """
    Эндпоинт для единоразовой привязки аккаунта Telegram.
    Требует email и пароль для подтверждения личности.
    """
    user = await service.link_telegram_account(
        email=credentials.username, password=credentials.password, tg_id=credentials.tg_id
    )

    return service.get_auth_token(user=user)


@router.post(path="/telegram/unlink/", status_code=status.HTTP_200_OK, summary="Отвязка ТГ-аккаунта от учетной записи")
async def unlink_telegram_account(
    payload: UserTelegramUnlink,
    service: AuthServiceDepends,
    system_secret_key: BotSecretHeader,
    redis: RedisConfigDepends,
):
    await service.unlink_telegram_account(tg_id=payload.tg_id, system_secret_key=system_secret_key, redis=redis)
    return {"message": f"TG аккаунт {payload.tg_id} отвязан от учетной записи"}


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
