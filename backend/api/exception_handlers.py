from typing import Literal

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from backend.core.utils.error_schemas import ErrorResponseSchema
from backend.exceptions import (
    AccessDeniedError,
    BadCredentialsError,
    CommentDoesNotExistsError,
    DatetimeMismatchError,
    EvaluationDoesNotExistError,
    InvalidPasswordError,
    MeetingDoesNotExistError,
    MeetingOverlapError,
    PasswordsMismatchError,
    RoleDoesNotExistError,
    TaskAlreadyEvaluatedError,
    TaskDoesNotExistError,
    TaskNotCompletedError,
    TeamAlreadyExistError,
    TeamDoesNotExistError,
    UnexpectedError,
    UnknownAccessLevelError,
    UserAlreadyActiveError,
    UserAlreadyInTeamError,
    UserDoesNotExistError,
    UserExistsError,
    UserNotActiveError,
)


def sqlalchemy_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Глобальный перехватчик любых непредвиденных ошибок базы данных.
    Прячет технические детали от клиента, но пишет полный трейсбэк в логи.
    """
    # Пишем в лог метод, URL и саму ошибку для дебага
    logger.error(
        f"Database error occurred while processing {request.method} {request.url.path} \nException details: {repr(exc)}"
    )
    content = ErrorResponseSchema(
        detail="Внутренняя ошибка базы данных. Пожалуйста, обратитесь в техническую поддержку.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    # Отдаем клиенту безопасный стандартизированный ответ
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content.model_dump(),
    )


# Единственная универсальная функция-фабрика
def create_exception_handler(status_code: int, log_level: Literal["ERROR", "WARNING", "INFO", "DEBUG"] = "WARNING"):
    def handler(request: Request, exc: Exception) -> JSONResponse:
        log_message = f"Ошибка {status_code} при {request.method} {request.url.path} | Детали: {exc}"

        logger.log(log_level, log_message)

        content = ErrorResponseSchema(detail=str(exc), status_code=status_code)

        return JSONResponse(
            status_code=status_code,
            content=content.model_dump(),
        )

    return handler


def setup_exception_handlers(app: FastAPI):
    # Ошибки 404
    app.add_exception_handler(TaskDoesNotExistError, create_exception_handler(status_code=status.HTTP_404_NOT_FOUND))
    app.add_exception_handler(TeamDoesNotExistError, create_exception_handler(status_code=status.HTTP_404_NOT_FOUND))
    app.add_exception_handler(MeetingDoesNotExistError, create_exception_handler(status_code=status.HTTP_404_NOT_FOUND))
    app.add_exception_handler(
        CommentDoesNotExistsError, create_exception_handler(status_code=status.HTTP_404_NOT_FOUND)
    )
    app.add_exception_handler(
        EvaluationDoesNotExistError, create_exception_handler(status_code=status.HTTP_404_NOT_FOUND)
    )

    # Ошибки 401
    app.add_exception_handler(BadCredentialsError, create_exception_handler(status_code=status.HTTP_401_UNAUTHORIZED))

    # Ошибки 403
    app.add_exception_handler(AccessDeniedError, create_exception_handler(status_code=status.HTTP_403_FORBIDDEN))
    app.add_exception_handler(UserNotActiveError, create_exception_handler(status_code=status.HTTP_403_FORBIDDEN))
    app.add_exception_handler(InvalidPasswordError, create_exception_handler(status_code=status.HTTP_403_FORBIDDEN))

    # Ошибки 400
    app.add_exception_handler(TeamAlreadyExistError, create_exception_handler(status_code=status.HTTP_400_BAD_REQUEST))
    app.add_exception_handler(UserAlreadyInTeamError, create_exception_handler(status_code=status.HTTP_400_BAD_REQUEST))
    app.add_exception_handler(UserDoesNotExistError, create_exception_handler(status_code=status.HTTP_400_BAD_REQUEST))
    app.add_exception_handler(UserExistsError, create_exception_handler(status_code=status.HTTP_400_BAD_REQUEST))
    app.add_exception_handler(PasswordsMismatchError, create_exception_handler(status_code=status.HTTP_400_BAD_REQUEST))
    app.add_exception_handler(TaskNotCompletedError, create_exception_handler(status_code=status.HTTP_400_BAD_REQUEST))
    app.add_exception_handler(
        TaskAlreadyEvaluatedError, create_exception_handler(status_code=status.HTTP_400_BAD_REQUEST)
    )
    app.add_exception_handler(DatetimeMismatchError, create_exception_handler(status_code=status.HTTP_400_BAD_REQUEST))

    # Ошибки 409
    app.add_exception_handler(UserAlreadyActiveError, create_exception_handler(status_code=status.HTTP_409_CONFLICT))
    app.add_exception_handler(MeetingOverlapError, create_exception_handler(status_code=status.HTTP_409_CONFLICT))

    # Ошибки 500 (внутренние доменные)
    app.add_exception_handler(
        RoleDoesNotExistError,
        create_exception_handler(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, log_level="ERROR"),
    )
    app.add_exception_handler(
        UnknownAccessLevelError,
        create_exception_handler(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, log_level="ERROR"),
    )
    app.add_exception_handler(
        UnexpectedError, create_exception_handler(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, log_level="ERROR")
    )

    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
