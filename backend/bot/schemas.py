from pydantic import BaseModel, Field

from backend.auth.schemas import UserLogin


class UserTelegramLogin(BaseModel):
    tg_id: int = Field(..., description="TelegramID пользователя")


class UserTelegramLink(UserLogin, UserTelegramLogin):
    pass


class UserTelegramUnlink(UserTelegramLogin):
    pass
