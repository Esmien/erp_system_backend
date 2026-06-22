from fastapi import Request
from sqladmin import ModelView

from backend.task.models import Task
from backend.team.models import Team
from backend.team.service import TeamService
from backend.user.models import User


class UserAdmin(ModelView, model=User):
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"

    # Что показываем в таблице
    column_list = [User.id, User.email, User.name, User.is_active, User.role_id]
    # По каким полям работает поиск
    column_searchable_list = [User.email, User.name]
    # Что можно сортировать
    column_sortable_list = [User.id, User.email]
    # Скрываем хэш пароля от редактирования в админке
    form_excluded_columns = [User.hashed_password]

    column_labels = {
        User.id: "ID",
        User.email: "Электронная почта",
        User.name: "Имя",
        User.surname: "Отчество",
        User.last_name: "Фамилия",
        User.is_active: "Статус",
        User.role: "Роль",
        User.team: "Команда",
    }


class TeamAdmin(ModelView, model=Team):
    name = "Команда"
    name_plural = "Команды"
    icon = "fa-solid fa-users"

    column_list = [Team.id, Team.name, Team.invite_code]
    form_excluded_columns = [Team.invite_code, Team.created_at]
    column_searchable_list = [Team.name]

    async def on_model_change(self, data: dict, model: Team, is_created: bool, request: Request) -> None:
        if is_created:
            data["invite_code"] = TeamService.generate_invite_code()


class TaskAdmin(ModelView, model=Task):
    name = "Задача"
    name_plural = "Задачи"
    icon = "fa-solid fa-list-check"

    column_list = [
        Task.id,
        Task.title,
        Task.status,
        Task.expire,
        Task.author,
        Task.executor,
    ]
    column_searchable_list = [Task.title]
    column_sortable_list = [Task.expire, Task.status]

    form_excluded_columns = [Task.created_at]
