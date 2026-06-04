from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, model_validator, Field

from backend.core.constants import MeetingStatus
from backend.exceptions import DatetimeCompatibleError
from backend.user.schemas import UserRead


class MeetingBase(BaseModel):
    """
    Базовая схема встречи
    """

    theme: str = Field(..., max_length=100, examples=["Планерка"])
    datetime_start: datetime
    datetime_end: datetime
    status: MeetingStatus = Field(
        default=MeetingStatus.PENDING,
        description="Статус встречи: Ожидается(PENDING), в процессе(IN_PROCESS), завершена(ENDS), отменена(CANCELED)",
    )
    participant_ids: list[int] = Field(
        default_factory=list, description="ID участников"
    )

    @model_validator(mode="after")
    def validate_datetime(self):
        """
        Валидирует дату для защиты от ошибочных значений.
        Нельзя выбрать дату в прошлом, а также указать дату/время завершения встречи раньше,
        чем начало
        """
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)

        # Конвертируем в UTC, если таймзона передана, иначе просто ставим метку UTC
        start_tz = (
            self.datetime_start.replace(tzinfo=timezone.utc)
            if self.datetime_start.tzinfo is None
            else self.datetime_start.astimezone(timezone.utc)
        )
        end_tz = (
            self.datetime_end.replace(tzinfo=timezone.utc)
            if self.datetime_end.tzinfo is None
            else self.datetime_end.astimezone(timezone.utc)
        )

        # Ограничиваем точность до минут
        start_tz = start_tz.replace(second=0, microsecond=0)

        if start_tz < now:
            raise DatetimeCompatibleError(
                "Встреча не может начаться раньше текущего времени"
            )

        if end_tz <= start_tz:
            raise DatetimeCompatibleError(
                "Встреча не может окончиться раньше или одновременно с началом"
            )

        return self


class MeetingCreate(MeetingBase):
    """Схема для FastAPI роутера (только то, что вводит юзер)"""

    pass


class MeetingCreateDTO(MeetingBase):
    """Схема для передачи из Сервиса в Репозиторий (полные данные)"""

    author_id: int


class MeetingReadWithParticipants(MeetingBase):
    """Схема отдачи данных встерчи со списком участников клиенту"""

    id: int
    author_id: int
    participants: list[UserRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class MeetingUpdate(BaseModel):
    """Схема для обновления встречи (все поля опциональны)"""

    theme: str | None = Field(default=None, max_length=100)
    datetime_start: datetime | None = None
    datetime_end: datetime | None = None
    status: MeetingStatus | None = None
    participant_ids: list[int] | None = Field(
        default=None, description="Новый список ID участников"
    )

    @model_validator(mode="after")
    def validate_datetime(self):
        now = datetime.now(timezone.utc)

        # Если передана дата начала, проверяем её на актуальность
        if self.datetime_start is not None:
            start_tz = (
                self.datetime_start.replace(tzinfo=timezone.utc)
                if self.datetime_start.tzinfo is None
                else self.datetime_start.astimezone(timezone.utc)
            )
            if start_tz < now:
                raise DatetimeCompatibleError(
                    "Встреча не может начаться раньше текущего времени"
                )

        # Проверяем, обе ли даты переданы и проверяем их на соответствие правилам:
        # начало не может быть позже завершения
        if self.datetime_start is not None and self.datetime_end is not None:
            start_tz = (
                self.datetime_start.replace(tzinfo=timezone.utc)
                if self.datetime_start.tzinfo is None
                else self.datetime_start.astimezone(timezone.utc)
            )
            end_tz = (
                self.datetime_end.replace(tzinfo=timezone.utc)
                if self.datetime_end.tzinfo is None
                else self.datetime_end.astimezone(timezone.utc)
            )

            if end_tz <= start_tz:
                raise DatetimeCompatibleError(
                    "Встреча не может окончиться раньше или одновременно с началом"
                )

        return self

    model_config = ConfigDict(extra="forbid")


class MeetingUpdateDTO(BaseModel):
    """Строгий контракт для передачи данных из Service в Repository"""

    theme: str | None = None
    datetime_start: datetime | None = None
    datetime_end: datetime | None = None
    status: MeetingStatus | None = None
    participant_ids: list[int] | None = None
