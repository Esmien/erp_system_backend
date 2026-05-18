from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.api.deps import get_current_user, RepositoryDepends
from backend.core.database.engine import get_session
from backend.core.database.models.users import User
from backend.core.schemas.user import UserRead, Token, UserRegister, UserChangeStatus
from backend.core.security import create_access_token, check_users_creds
from backend.core.schemas.error_schemas import ErrorResponseSchema
from backend.exceptions import UserExistsError, RoleDoesNotExistsError

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
    repo: RepositoryDepends,
):
    """
    Регистрирует пользователя, назначая ему по умолчанию роль "user"
    """

    try:
        new_user = await repo.register_user(user_in=user_in)
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
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    """
    Восстанавливает активность пользователя после 'мягкого' удаления

    Args:
        form_data (OAuth2PasswordRequestForm): Данные для восстановления
        session (AsyncSession): Сессия БД

    Raises:
        HTTPException: Если пользователь не найден (404), уже активен (409) или неверный пароль (401)

    Returns:
        UserChangeStatus: Восстановленный пользователь и сообщение об успешном восстановлении
    """

    user = await check_users_creds(form_data.username, form_data.password, session)

    if user.is_active:
        logger.warning(f"Пользователь {user.name} уже активен")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Пользователь уже активен"
        )

    user.is_active = True

    session.add(user)
    await session.commit()
    await session.refresh(user)

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
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    """
    Аутентификация пользователя

    Args:
        form_data (OAuth2PasswordRequestForm): Данные для аутентификации
        session (AsyncSession): Сессия БД

    Raises:
        HTTPException: Если пользователь не найден или не активен (401)

    Returns:
        Token: Токен доступа
    """

    user = await check_users_creds(form_data.username, form_data.password, session)

    # Проверяем активность пользователя
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не активен",
        )

    # Создаем токен доступа
    access_token = create_access_token(data={"sub": str(user.id)})

    return Token(access_token=access_token, token_type="bearer")


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
