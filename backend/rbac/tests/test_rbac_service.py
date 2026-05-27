import pytest
from backend.rbac.schemas import AccessRuleDTO


@pytest.mark.parametrize(
    "rule_exists, permission_name, permission_value, expected_result",
    [
        (True, "read_permission", True, True),  # Правило есть, право выдано
        (True, "create_permission", False, False),  # Правило есть, права НЕТ
        (
            True,
            "unknown_permission",
            False,
            False,
        ),  # Запрос кривого/несуществующего permission
        (
            False,
            "read_permission",
            False,
            False,
        ),  # Правила для роли/ресурса вообще нет в БД
    ],
)
async def test_check_permission(
    rbac_service,
    mock_uow,
    rule_exists,
    permission_name,
    permission_value,
    expected_result,
):
    if rule_exists:
        # Имитируем DTO, которое возвращает репозиторий
        rule_data = {
            "id": 1,
            "business_element_id": 1,
            "role_id": 1,
            "read_permission": False,
            "create_permission": False,
        }
        # Если тест проверяет валидное поле, подменяем его значением из параметров
        if permission_name in rule_data:
            rule_data[permission_name] = permission_value

        mock_uow.rbac.get_access_rule.return_value = AccessRuleDTO(**rule_data)
    else:
        mock_uow.rbac.get_access_rule.return_value = None

    # Вызываем тестируемый метод
    result = await rbac_service.check_permission(
        role_id=1, element_name="teams", permission=permission_name
    )

    # Проверки
    assert result is expected_result
    mock_uow.rbac.get_access_rule.assert_called_once_with(1, "teams")
