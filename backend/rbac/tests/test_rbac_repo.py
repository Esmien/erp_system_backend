import pytest


@pytest.mark.parametrize(
    "role_id, element_name, expected_found",
    [(1, "teams", True), (999, "teams", False), (1, "unknown_element", False)],
)
async def test_get_access_rule(rbac_repo, role_id, element_name, expected_found):
    rule = await rbac_repo.get_access_rule(role_id=role_id, element_name=element_name)

    if expected_found:
        assert rule is not None
        assert rule.role_id == role_id
        assert rule.business_element_id == 1
    else:
        assert rule is None
