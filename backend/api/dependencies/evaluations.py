from typing import Annotated

from fastapi import Body, Depends

from backend.api.dependencies.rbac import RbacServiceDepends
from backend.api.dependencies.uow import UowDepends
from backend.evaluation.schemas import EvaluationCreate
from backend.evaluation.service import EvaluationService


def get_evaluation_service(uow: UowDepends, rbac_service: RbacServiceDepends) -> EvaluationService:
    return EvaluationService(uow=uow, rbac_service=rbac_service)


EvaluationServiceDepends = Annotated[EvaluationService, Depends(get_evaluation_service)]
EvaluationCreateBody = Annotated[EvaluationCreate, Body()]
