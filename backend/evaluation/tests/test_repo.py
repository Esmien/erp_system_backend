from backend.core.enums import TaskStatus
from backend.evaluation.models import Evaluation
from backend.evaluation.schemas import EvaluationCreateDTO
from backend.task.models import Task


async def test_repository_add_and_get(eval_repo, test_task_db, test_user_db):
    dto_in = EvaluationCreateDTO(
        value=4,
        comment="Test repo",
        task_id=test_task_db.id,
        evaluator_id=test_user_db.id,
    )

    saved_eval = await eval_repo.create(**dto_in.model_dump())

    assert saved_eval.id is not None
    assert saved_eval.value == 4
    assert saved_eval.comment == "Test repo"

    fetched_eval = await eval_repo.get_by_task_id(test_task_db.id)

    assert fetched_eval is not None
    assert fetched_eval.id == saved_eval.id
    assert fetched_eval.task_id == test_task_db.id


async def test_repository_get_user_statistics_empty(eval_repo, test_user_db):
    # У юзера еще нет оценок
    stats = await eval_repo.get_user_statistics(test_user_db.id)

    assert stats.average_evaluation == 0
    assert stats.tasks_evaluated_count == 0


async def test_repository_get_user_statistics_calculated(
    eval_repo, db_session, test_user_db
):
    # 1. Создаем две задачи, где наш тестовый юзер — исполнитель
    task1 = Task(
        title="T1",
        description="D1",
        author_id=test_user_db.id,
        executor_id=test_user_db.id,
        status=TaskStatus.DONE,
    )
    task2 = Task(
        title="T2",
        description="D2",
        author_id=test_user_db.id,
        executor_id=test_user_db.id,
        status=TaskStatus.DONE,
    )
    db_session.add_all([task1, task2])
    await db_session.flush()

    # 2. Ставим оценки (4 и 5)
    eval1 = Evaluation(value=4, task_id=task1.id, evaluator_id=test_user_db.id)
    eval2 = Evaluation(value=5, task_id=task2.id, evaluator_id=test_user_db.id)
    db_session.add_all([eval1, eval2])
    await db_session.flush()

    # 3. Проверяем агрегацию
    stats = await eval_repo.get_user_statistics(test_user_db.id)

    assert stats.average_evaluation == 4.5
    assert stats.tasks_evaluated_count == 2
