import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from backend.core.config import settings, RoleName
from backend.core.database.models.users import User
from backend.exceptions import UserDoesNotExistsError, UserNotActiveError

from backend.api.dependencies.reg_and_auth import AuthServiceDepends
from backend.api.dependencies.rbac import RbacServiceDepends

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthServiceDepends = None,
) -> User:
    """Возвращает текущего активного пользователя по JWT токену"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ошибка валидации токена",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    try:
        user = await auth_service.get_active_user_by_id(int(user_id))
        return user
    except (UserDoesNotExistsError, UserNotActiveError):
        raise credentials_exception


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Проверяет, является ли пользователь админом"""
    if current_user.role.name.value != RoleName.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Для выполнения этого действия необходимы права администратора",
        )
    return current_user


class PermissionChecker:
    """Динамический чекер прав доступа через RBAC"""

    def __init__(self, business_element: str, permission: str):
        self.business_element = business_element
        self.permission = permission

    async def __call__(
        self,
        user: User = Depends(get_current_user),
        rbac_service: RbacServiceDepends = None,
    ) -> User:

        has_access = await rbac_service.check_permission(
            role_id=user.role_id,
            element_name=self.business_element,
            permission=self.permission,
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав на выполнение этого действия",
            )

        return user
