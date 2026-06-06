import pytest
from unittest.mock import MagicMock

from backend.api.dependencies.evaluations import EvaluationCreateBody
from backend.core.constants import (
    TaskStatus,
    TASK_NOT_FOUND,
    BusinessElementName,
    Action,
)
from backend.evaluation.schemas import (
    EvaluationCreate,
    UserStatisticsRead,
)
from backend.exceptions import (
    AccessDeniedError,
    TaskDoesNotCompletedError,
    TaskDoesNotExistsError,
    TaskAlreadyEvaluatedError,
)
from backend.rbac.schemas import AccessContextDTO


async def test_evaluate_task_access_denied(eval_service, test_user):
    # Принудительно забираем права для этого теста
    eval_service.rbac.enforce_permission.side_effect = AccessDeniedError

    evaluation_in = EvaluationCreate(value=5, comment="Test")

    with pytest.raises(AccessDeniedError):
        await eval_service.evaluate_task(
            task_id=1, evaluation_in=evaluation_in, user=test_user
        )


async def test_evaluate_task_not_completed(eval_service, mock_uow, test_user):
    mock_task = MagicMock()
    mock_task.status = TaskStatus.OPEN
    mock_uow.tasks.get_task_by_id.return_value = mock_task

    evaluation_in = EvaluationCreate(value=5)

    with pytest.raises(TaskDoesNotCompletedError, match="Задача еще не выполнена"):
        await eval_service.evaluate_task(
            task_id=1, evaluation_in=evaluation_in, user=test_user
        )


async def test_evaluate_task_success(eval_service, mock_uow, test_user):
    mock_task = MagicMock()
    mock_task.status = TaskStatus.DONE
    mock_uow.tasks.get_by_id.return_value = mock_task
    mock_uow.evaluations.get_by_task_id.return_value = None

    mock_uow.evaluations.create.return_value = "saved_evaluation_mock"

    evaluation_in = EvaluationCreate(value=5, comment="Good")

    result = await eval_service.evaluate_task(
        task_id=1, evaluation_in=evaluation_in, user=test_user
    )

    mock_uow.commit.assert_awaited_once()
    assert result == "saved_evaluation_mock"

    # Проверяем, что в репозиторий улетели правильные данные
    kwargs = mock_uow.evaluations.create.call_args.kwargs
    assert kwargs.get("value") == 5
    assert kwargs.get("comment") == "Good"
    assert kwargs.get("task_id") == 1
    assert kwargs.get("evaluator_id") == test_user.id


async def test_get_my_statistics(eval_service, mock_uow, test_user):
    # Настраиваем мок репозитория
    mock_stats = UserStatisticsRead(average_evaluation=4.8, tasks_evaluated_count=10)
    mock_uow.evaluations.get_user_statistics.return_value = mock_stats

    # Вызываем сервис
    result = await eval_service.get_my_statistics(user=test_user)

    # Проверяем, что UoW был вызван с правильным ID и вернул нужный DTO
    mock_uow.evaluations.get_user_statistics.assert_awaited_once_with(
        user_id=test_user.id
    )
    assert result.average_evaluation == 4.8
    assert result.tasks_evaluated_count == 10


async def test_evaluate_task_not_found(eval_service, mock_uow, test_user):
    # Мокаем отсутствие задачи
    mock_uow.tasks.get_by_id.return_value = None
    evaluation_in = EvaluationCreateBody(value=5)

    with pytest.raises(TaskDoesNotExistsError, match=TASK_NOT_FOUND):
        await eval_service.evaluate_task(
            task_id=999, evaluation_in=evaluation_in, user=test_user
        )


async def test_evaluate_task_already_evaluated(eval_service, mock_uow, test_user):
    # Задача есть и завершена
    mock_task = MagicMock()
    mock_task.status = TaskStatus.DONE
    mock_uow.tasks.get_by_id.return_value = mock_task

    # НО оценка УЖЕ существует
    mock_uow.evaluations.get_by_task_id.return_value = MagicMock()
    evaluation_in = EvaluationCreateBody(value=5)

    with pytest.raises(TaskAlreadyEvaluatedError, match="Эта задача уже оценена"):
        await eval_service.evaluate_task(
            task_id=1, evaluation_in=evaluation_in, user=test_user
        )


async def test_get_evaluation_task_not_found(eval_service, mock_uow, test_user):
    # Пытаемся получить оценку несуществующей задачи
    mock_uow.tasks.get_by_id.return_value = None

    with pytest.raises(TaskDoesNotExistsError, match=TASK_NOT_FOUND):
        await eval_service.get_evaluation(task_id=999, user=test_user)


async def test_get_evaluation_access_denied(eval_service, mock_uow, test_user):
    # Задача есть
    mock_task = MagicMock()
    mock_task.author_id = 99
    mock_task.executor_id = 100
    mock_uow.tasks.get_by_id.return_value = mock_task

    # RBAC жестко режет права (например, обычный юзер лезет в чужую задачу)
    eval_service.rbac.enforce_permission.side_effect = AccessDeniedError

    with pytest.raises(AccessDeniedError):
        await eval_service.get_evaluation(task_id=1, user=test_user)


async def test_get_evaluation_success(eval_service, mock_uow, test_user):
    # Идеальный путь: задача есть, юзер - участник
    mock_task = MagicMock()
    mock_task.author_id = test_user.id  # Совпадает с ID текущего пользователя
    mock_task.executor_id = 99
    mock_uow.tasks.get_by_id.return_value = mock_task

    # Репозиторий возвращает оценку
    expected_eval = MagicMock()
    mock_uow.evaluations.get_by_task_id.return_value = expected_eval

    # Вызов
    result = await eval_service.get_evaluation(task_id=1, user=test_user)

    assert result == expected_eval

    # Проверяем, что в RBAC улетел правильный контекст
    eval_service.rbac.enforce_permission.assert_awaited_once_with(
        user=test_user,
        business_element_name=BusinessElementName.EVALUATIONS,
        action=Action.READ,
        context=AccessContextDTO(is_participant=True),
        error_msg="У вас нет прав для просмотра этой оценки",
    )
