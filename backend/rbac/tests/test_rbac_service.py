import pytest

from backend.core.enums import BusinessElementName
from backend.core.policies import AccessLevel
from backend.rbac.schemas import AccessContextDTO, AccessRuleDTO


@pytest.mark.parametrize(
    "rule_exists, action, rule_access, context, expected_result",
    [
        (True, "read", AccessLevel.ALL, None, True),  # Доступ разрешен всем
        (
            True,
            "create",
            AccessLevel.PARTICIPANT,
            AccessContextDTO(is_participant=True),
            True,
        ),  # Участник может создать
        (
            True,
            "create",
            AccessLevel.PARTICIPANT,
            AccessContextDTO(is_participant=False),
            False,
        ),  # Не участник - отказ
        (
            True,
            "update",
            AccessLevel.AUTHOR,
            AccessContextDTO(is_author=True),
            True,
        ),  # Автор может обновить
        (True, "unknown_action", AccessLevel.ALL, None, False),  # Неизвестное действие
        (False, "read", None, None, False),  # Правила нет в БД
    ],
)
async def test_check_permission(rbac_service, mock_uow, rule_exists, action, rule_access, context, expected_result):
    if rule_exists:
        # Если проверяем неизвестное действие, кладем в базу валидное (например, "read"),
        # чтобы неизвестного действия там точно не оказалось.
        policy_dict = {"read": rule_access} if action == "unknown_action" else {action: rule_access}

        rule_data = {
            "id": 1,
            "business_element_id": 1,
            "role_id": 1,
            "policies": policy_dict if rule_access else {},
        }
        mock_uow.rbac.get_access_rule.return_value = AccessRuleDTO(**rule_data)
    else:
        mock_uow.rbac.get_access_rule.return_value = None

    result = await rbac_service.check_permission(
        role_id=1,
        business_element_name=BusinessElementName.TASKS,
        action=action,
        context=context,
    )

    assert result is expected_result
