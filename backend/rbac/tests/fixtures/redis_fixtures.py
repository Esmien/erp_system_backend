import pytest

from backend.rbac.schemas import AccessRuleDTO


@pytest.fixture
def dummy_rule() -> AccessRuleDTO:
    """Фикстура с тестовым правилом доступа"""
    return AccessRuleDTO(
        id=1, role_id=1, business_element_id=1, policies={"read": 3, "write": 3}
    )
