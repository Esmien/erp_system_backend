from unittest.mock import AsyncMock

from backend.core.config import Settings
from backend.core.enums import BusinessElementName
from backend.rbac.schemas import AccessRuleDTO
from backend.rbac.service import RbacService


async def test_get_rule_cache_miss_saves_to_redis(
    rbac_service: RbacService,
    mock_uow: AsyncMock,
    mock_redis: AsyncMock,
    dummy_rule: AccessRuleDTO,
    mock_settings: Settings,
):
    """
    Сценарий 1: Данных в кэше нет.
    Ожидаем: запрос в БД и последующую запись в Redis.
    """
    # Настраиваем моки
    mock_redis.get.return_value = None
    mock_uow.rbac.get_access_rule.return_value = dummy_rule
    redis_rbac_key = mock_settings.redis_keys.key_rbac_rule(role_id=1, business_element_name=BusinessElementName.TASKS)

    # Вызываем метод
    result = await rbac_service._get_rule(role_id=1, business_element_name=BusinessElementName.TASKS)

    # Проверки
    assert result == dummy_rule

    # Убеждаемся, что мы попытались прочитать кэш
    mock_redis.get.assert_called_once_with(redis_rbac_key)

    # Убеждаемся, что мы сходили в БД
    mock_uow.rbac.get_access_rule.assert_called_once_with(role_id=1, business_element_name=BusinessElementName.TASKS)

    # Убеждаемся, что данные были записаны в кэш с правильным ключом
    mock_redis.setex.assert_called_once()
    args, kwargs = mock_redis.setex.call_args
    assert kwargs["name"] == redis_rbac_key
    assert kwargs["value"] == dummy_rule.model_dump_json()


async def test_get_rule_cache_hit_bypasses_db(
    rbac_service: RbacService,
    mock_uow: AsyncMock,
    mock_redis: AsyncMock,
    dummy_rule: AccessRuleDTO,
    mock_settings: Settings,
):
    """
    Сценарий 2: Данные есть в кэше.
    Ожидаем: возврат данных из кэша без запроса к БД.
    """
    # Настраиваем моки (Redis возвращает JSON-строку)
    mock_redis.get.return_value = dummy_rule.model_dump_json()
    redis_rbac_key = mock_settings.redis_keys.key_rbac_rule(role_id=1, business_element_name=BusinessElementName.TASKS)

    # Вызываем метод
    result = await rbac_service._get_rule(role_id=1, business_element_name=BusinessElementName.TASKS)

    # Проверки
    # Убеждаемся, что Pydantic-модель корректно собралась из строки
    assert result.id == dummy_rule.id
    assert result.policies == dummy_rule.policies

    mock_redis.get.assert_called_once_with(redis_rbac_key)

    # САМОЕ ВАЖНОЕ: Убеждаемся, что в базу запроса НЕ БЫЛО
    mock_uow.rbac.get_access_rule.assert_not_called()

    # Перезаписывать кэш тоже не должны были
    mock_redis.setex.assert_not_called()


async def test_get_rule_not_found_in_db(rbac_service: RbacService, mock_uow: AsyncMock, mock_redis: AsyncMock):
    """
    Сценарий 3: Промах кэша, и в БД такого правила тоже нет.
    Ожидаем: кэш не перезаписывается пустым значением.
    """
    mock_redis.get.return_value = None
    mock_uow.rbac.get_access_rule.return_value = None

    result = await rbac_service._get_rule(role_id=999, business_element_name=BusinessElementName.TASKS)

    assert result is None
    mock_redis.get.assert_called_once()
    mock_uow.rbac.get_access_rule.assert_called_once()

    # Убеждаемся, что пустой результат не полетел в Redis
    mock_redis.setex.assert_not_called()
