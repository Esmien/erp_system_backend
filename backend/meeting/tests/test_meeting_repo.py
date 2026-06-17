from datetime import datetime, timedelta, timezone


from backend.meeting.repository import MeetingRepository
from backend.meeting.schemas import MeetingCreateDTO, MeetingUpdateDTO
from backend.user.models import User


class TestMeetingRepository:
    """
    Полный набор тестов для слоя данных (MeetingRepository).
    Проверяет все CRUD-операции, работу со связями (participants) и фильтрации.
    """

    async def test_create_and_get_meeting(
        self, meeting_repo: MeetingRepository, test_users: list[User]
    ):
        author_id = test_users[0].id
        participant_ids = [test_users[1].id]

        start = datetime.now(timezone.utc) + timedelta(days=1)
        end = start + timedelta(hours=1)

        meeting_dto = MeetingCreateDTO(
            theme="Интеграционный тест",
            datetime_start=start,
            datetime_end=end,
            author_id=author_id,
            participant_ids=participant_ids,
        )

        # Тестируем создание
        created_meeting = await meeting_repo.create_meeting(meeting_dto)
        assert created_meeting.id is not None
        assert created_meeting.theme == "Интеграционный тест"
        assert len(created_meeting.participants) == 1
        assert created_meeting.participants[0].id == participant_ids[0]

        # Тестируем получение
        fetched_meeting = await meeting_repo.get_by_id(obj_id=created_meeting.id)
        assert fetched_meeting is not None
        assert fetched_meeting.id == created_meeting.id

    async def test_create_meeting_without_participants(
        self, meeting_repo: MeetingRepository, test_users: list[User]
    ):
        """
        Гарантирует отсутствие ошибки MissingGreenlet при создании встречи без участников (пустой список).
        """
        start = datetime.now(timezone.utc) + timedelta(days=1)
        end = start + timedelta(hours=1)

        meeting_dto = MeetingCreateDTO(
            theme="Встреча интроверта",
            datetime_start=start,
            datetime_end=end,
            author_id=test_users[0].id,
            participant_ids=[],  # Явно пустой список
        )

        created_meeting = await meeting_repo.create_meeting(meeting_dto)

        assert created_meeting.id is not None
        assert created_meeting.theme == "Встреча интроверта"
        assert len(created_meeting.participants) == 0

    async def test_get_overlapping_participants(
        self, meeting_repo: MeetingRepository, test_users: list[User]
    ):
        # 1. Создаем встречу с 10:00 до 11:00 (условно)
        start_1 = datetime.now(timezone.utc) + timedelta(days=2)
        end_1 = start_1 + timedelta(hours=1)

        await meeting_repo.create_meeting(
            MeetingCreateDTO(
                theme="Встреча 1",
                datetime_start=start_1,
                datetime_end=end_1,
                author_id=test_users[0].id,
                participant_ids=[test_users[1].id],
            )
        )

        # 2. Пытаемся проверить пересечение для новой встречи с 10:30 до 11:30 (Пересекается!)
        start_overlap = start_1 + timedelta(minutes=30)
        end_overlap = start_overlap + timedelta(hours=1)

        overlaps = await meeting_repo.get_overlapping_participants(
            participant_ids=[test_users[1].id],
            starts_on=start_overlap,
            ends_on=end_overlap,
        )

        assert test_users[1].id in overlaps

        # 3. Проверяем непересекающееся время
        start_no_overlap = end_1 + timedelta(hours=1)
        end_no_overlap = start_no_overlap + timedelta(hours=1)

        no_overlaps = await meeting_repo.get_overlapping_participants(
            participant_ids=[test_users[1].id],
            starts_on=start_no_overlap,
            ends_on=end_no_overlap,
        )
        assert len(no_overlaps) == 0

    async def test_update_meeting_participants(
        self, meeting_repo: MeetingRepository, test_users: list[User]
    ):
        # Создаем базу
        start = datetime.now(timezone.utc) + timedelta(days=3)
        end = start + timedelta(hours=1)
        meeting = await meeting_repo.create_meeting(
            MeetingCreateDTO(
                theme="Старая тема",
                datetime_start=start,
                datetime_end=end,
                author_id=test_users[0].id,
                participant_ids=[test_users[1].id],
            )
        )

        # Обновляем тему и полностью меняем список участников
        update_dto = MeetingUpdateDTO(
            theme="Новая тема", participant_ids=[test_users[2].id]
        )

        updated = await meeting_repo.update_meeting(
            meeting_id=meeting.id, data_for_update=update_dto
        )

        assert updated is not None
        assert updated.theme == "Новая тема"
        # Старый участник удален, новый добавлен
        assert len(updated.participants) == 1
        assert updated.participants[0].id == test_users[2].id

    async def test_get_meetings(
        self, meeting_repo: MeetingRepository, test_users: list[User]
    ):
        start = datetime.now(timezone.utc)

        # 1. Создаем встречу: Автор [0], Участник [1]
        await meeting_repo.create_meeting(
            MeetingCreateDTO(
                theme="Синхронизация команд",
                datetime_start=start,
                datetime_end=start + timedelta(hours=1),
                author_id=test_users[0].id,
                participant_ids=[test_users[1].id],
            )
        )

        # 2. Создаем встречу: Автор [2], без участников
        await meeting_repo.create_meeting(
            MeetingCreateDTO(
                theme="Личная задача",
                datetime_start=start,
                datetime_end=start + timedelta(hours=1),
                author_id=test_users[2].id,
                participant_ids=[],
            )
        )

        # Запрос без фильтра (как работает админ/менеджер)
        all_meetings, total = await meeting_repo.get_meetings(
            user_id=None, offset=0, limit=20
        )
        assert len(all_meetings) >= 2

        # Запрос с фильтром (пользователь 1 видит только то, где он участник)
        user_1_meetings, totl = await meeting_repo.get_meetings(
            user_id=test_users[1].id, offset=0, limit=20
        )
        assert len(user_1_meetings) == 1
        assert user_1_meetings[0].theme == "Синхронизация команд"

    async def test_delete_meeting(
        self, meeting_repo: MeetingRepository, test_users: list[User]
    ):
        start = datetime.now(timezone.utc)
        meeting = await meeting_repo.create_meeting(
            MeetingCreateDTO(
                theme="Отмененная встреча",
                datetime_start=start,
                datetime_end=start + timedelta(hours=1),
                author_id=test_users[0].id,
                participant_ids=[],
            )
        )

        # Убеждаемся, что она есть
        assert await meeting_repo.get_by_id(obj_id=meeting.id) is not None

        # Удаляем
        await meeting_repo.delete(obj_id=meeting.id)

        # Пытаемся получить снова
        fetched = await meeting_repo.get_by_id(obj_id=meeting.id)
        assert fetched is None

    async def test_get_meetings_by_date_range(
        self, meeting_repo: MeetingRepository, test_users: list[User]
    ):
        base_time = datetime.now(timezone.utc)
        user_id = test_users[0].id

        # Встреча "завтра" (попадает в диапазон)
        await meeting_repo.create_meeting(
            MeetingCreateDTO(
                theme="В диапазоне",
                datetime_start=base_time + timedelta(days=1),
                datetime_end=base_time + timedelta(days=1, hours=1),
                author_id=user_id,
                participant_ids=[],
            )
        )

        # Встреча через неделю (не попадает в диапазон)
        await meeting_repo.create_meeting(
            MeetingCreateDTO(
                theme="Вне диапазона",
                datetime_start=base_time + timedelta(days=7),
                datetime_end=base_time + timedelta(days=7, hours=1),
                author_id=user_id,
                participant_ids=[],
            )
        )

        # Ищем встречи за ближайшие 3 дня
        meetings = await meeting_repo.get_meetings_by_date_range(
            user_id=user_id,
            start_date=base_time,
            end_date=base_time + timedelta(days=3),
        )

        assert len(meetings) == 1
        assert meetings[0].theme == "В диапазоне"
