from fastapi import APIRouter, status

from backend.bot.api.dependencies import BotAuthServiceDepends, BotSecretHeader
from backend.bot.schemas import UserTelegramLink, UserTelegramLogin, UserTelegramUnlink
from backend.core.utils.error_schemas import ErrorResponseSchema
from backend.user.schemas import Token

router = APIRouter(prefix="/telegram", tags=["Telegram BOT"])


@router.post(
    path="/login/",
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
    service: BotAuthServiceDepends,
    credentials: UserTelegramLogin,
):
    """
    Аутентификация пользователя через телеграм-бота
    Нет связи TGID и аккаунта ERP - 401 Unauthorized
    Пользователь есть, но неактивен - 403 Forbidden
    """
    user = await service.authenticate_by_telegram(tg_id=credentials.tg_id)

    return service.api_auth_service.get_auth_tokens(user=user)


@router.post(
    path="/link/",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Привязка Telegram ID к аккаунту",
    responses={
        401: {
            "model": ErrorResponseSchema,
            "description": "Неверные данные учетной записи или пользователь не существует",
        },
        500: {"model": ErrorResponseSchema, "description": "Неизвестная ошибка при привязке TGID к аккаунту ERP"},
    },
)
async def link_telegram_account(
    service: BotAuthServiceDepends,
    credentials: UserTelegramLink,
):
    """
    Эндпоинт для единоразовой привязки аккаунта Telegram.
    Требует email и пароль для подтверждения личности.
    Неверные креды - 401 Unauthorized
    Сбой привязки - 500 Internal Server Error
    """
    user = await service.link_telegram_account(
        email=credentials.username, password=credentials.password, tg_id=credentials.tg_id
    )

    return service.api_auth_service.get_auth_tokens(user=user)


@router.post(
    path="/unlink/",
    status_code=status.HTTP_200_OK,
    summary="Отвязка ТГ-аккаунта от учетной записи",
    responses={
        401: {
            "model": ErrorResponseSchema,
            "description": "Неверный системный ключ",
        },
    },
)
async def unlink_telegram_account(
    payload: UserTelegramUnlink,
    service: BotAuthServiceDepends,
    system_secret_key: BotSecretHeader,
):
    """Отвязывает TGID от аккаунта ERP"""
    await service.unlink_telegram_account(tg_id=payload.tg_id, system_secret_key=system_secret_key)
    return {"message": f"TG аккаунт {payload.tg_id} отвязан от учетной записи"}
