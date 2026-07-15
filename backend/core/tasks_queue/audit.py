from loguru import logger

from backend.api.dependencies.uow import UowDepends
from backend.core.tasks_queue.broker import broker
from backend.core.tasks_queue.core_models import AuditLog


@broker.task(task_name="audit_log_task")
async def log_audit_action(
    user_id: int,
    action: str,
    entity_name: str,
    entity_id: int,
    uow: UowDepends,
) -> None:
    """
    Асинхронная задача для обработки логов аудита.
    Пока просто пишем в лог, в будущем — сохраняем в таблицу audit_logs.
    """
    logger.info(f"Сохраняем в БД действие '{action}' от юзера {user_id}")

    # Создаем запись в базе
    new_log = AuditLog(user_id=user_id, action=action, entity_name=entity_name, entity_id=entity_id)

    async with uow:
        uow.session.add(instance=new_log)
        await uow.session.commit()

    logger.info("Запись успешно сохранена в AuditLog")
