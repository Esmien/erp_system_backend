from fastapi import APIRouter, status
from loguru import logger

from backend.api.dependencies.permissions import CurrentUserDepends
from backend.api.dependencies.reg_and_auth import RegisterServiceDepends
from backend.core.utils.error_schemas import ErrorResponseSchema
from backend.user.schemas import RegisterCode

router = APIRouter(prefix="/register_code", tags=["Код регистрации"])


@router.post(
    path="/generate/",
    status_code=status.HTTP_201_CREATED,
    response_model=RegisterCode,
    summary="Генерация кода регистрации (Только для админов)",
)
async def generate_registration_code(current_user: CurrentUserDepends, service: RegisterServiceDepends):
    # Генерируем случайную строку из 6 символов (заглавные буквы и цифры)
    new_code = await service.generate_registration_code(user=current_user)
    logger.info(f"Сгенерирован новый регистрационный код: {new_code}")
    return new_code


@router.get(
    path="/{code}/validate/",
    status_code=status.HTTP_200_OK,
    responses={
        403: {
            "model": ErrorResponseSchema,
            "description": "Код не существует или истек",
        },
    },
    summary="Проверка валидности кода регистрации",
)
async def validate_registration_code(code: str, service: RegisterServiceDepends):
    await service.validate_registration_code(code=code)

    return {"status": "ok", "message": "Код действителен"}
