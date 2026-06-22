from loguru import logger

from backend.core.database.engine import Base


def load_all_models() -> tuple:
    """
    Принудительная загрузка всех моделей в память.
    Необходима для корректной работы маппера SQLAlchemy и резолва связей.
    """
    from backend.comment.models import Comment
    from backend.evaluation.models import Evaluation
    from backend.meeting.models import Meeting
    from backend.rbac.models import AccessRule, BusinessElement
    from backend.task.models import Task
    from backend.team.models import Team
    from backend.user.models import Role, User

    logger.info("Реестр моделей SQLAlchemy успешно инициализирован")

    return (
        User,
        Role,
        Team,
        Task,
        Comment,
        AccessRule,
        BusinessElement,
        Evaluation,
        Meeting,
    )


__all__ = ["Base", "load_all_models"]
