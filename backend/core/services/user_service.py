from backend.core.database.models import User
from backend.core.database.repository.user import UserRepository
from backend.core.schemas.user import UserUpdate


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def update_profile(self, user: User, update_data: UserUpdate) -> User:
        update_dict = update_data.model_dump(exclude_unset=True)

        if not update_dict:
            return user

        for key, value in update_dict.items():
            setattr(user, key, value)

        return await self.repo.update_user(user)
