import jwt
from fastapi import Request
from jwt.exceptions import PyJWTError
from sqladmin.authentication import AuthenticationBackend

from backend.core.config import settings
from backend.core.enums import RoleName
from backend.core.uow import UnitOfWork
from backend.exceptions import BadCredentialsError
from backend.user.service import AuthService


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email, password = str(form["username"]), str(form["password"])

        async with UnitOfWork() as uow:
            service = AuthService(uow=uow)

            try:
                user = await service.check_users_creds(email=email, password=password)
            except BadCredentialsError:
                return False

            if user.role.name != RoleName.ADMIN:
                return False

            # Генерируем токен
            token_obj = service.get_auth_token(user=user)

            # Сохраняем в сессию браузера
            request.session.update({"token": token_obj.access_token})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        try:
            jwt.decode(
                jwt=token,
                key=settings.security.SECRET_KEY,
                algorithms=settings.security.ALGORITHM,
            )
        except PyJWTError:
            # Токен протух, подпись не совпала или он поврежден
            return False

        return True
