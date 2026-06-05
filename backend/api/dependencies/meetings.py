from typing import Annotated

from fastapi import Depends, Body

from backend.api.dependencies.rbac import RbacServiceDepends
from backend.api.dependencies.uow import UowDepends
from backend.meeting.schemas import MeetingCreate, MeetingUpdate
from backend.meeting.service import MeetingService


def get_meeting_service(
    uow: UowDepends, rbac_service: RbacServiceDepends
) -> MeetingService:
    """Провайдер сервиса для работы со встречами для инъекции в Annotated"""
    return MeetingService(uow=uow, rbac_service=rbac_service)


# Готовые DI для использования в роутерах
MeetingServiceDepends = Annotated[MeetingService, Depends(get_meeting_service)]
MeetingCreateBody = Annotated[MeetingCreate, Body()]
MeetingUpdateBody = Annotated[MeetingUpdate, Body()]
