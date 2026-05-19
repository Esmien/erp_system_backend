from fastapi import APIRouter, status

from backend.api.dependencies.users import CurrentUserDepends
from backend.core.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get(
    path="/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Получить инфо о себе",
)
async def get_my_info(current_user: CurrentUserDepends):
    return current_user
