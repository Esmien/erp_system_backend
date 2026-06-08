from fastapi import Request, status, FastAPI
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from backend.exceptions import (
    UserDoesNotExistsError,
    TaskDoesNotExistsError,
    TeamDoesNotExistsError,
    RoleDoesNotExistsError,
    AccessDeniedError,
    UserNotActiveError,
    TeamAlreadyExistsError,
    UserAlreadyInTeamError,
    UserExistsError,
    UserAlreadyActiveError,
    BadCredentialsError,
    PasswordsMismatchError,
    TaskAlreadyEvaluatedError,
    TaskDoesNotCompletedError,
    MeetingOverlapError,
    MeetingDoesNotExistsError,
    DatetimeCompatibleError,
    UnknownAccessLevelError,
    InvalidPasswordError,
    CommentDoesNotExistsError,
    EvaluationDoesNotExistsError,
)


def not_found_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


def internal_server_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


def not_authorized_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
    )


def access_denied_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)},
    )


def bad_request_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


def conflict_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


def sqlalchemy_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Глобальный перехватчик любых непредвиденных ошибок базы данных.
    Прячет технические детали от клиента, но пишет полный трейсбэк в логи.
    """
    # Пишем в лог метод, URL и саму ошибку для дебага
    logger.error(
        f"Database error occurred while processing {request.method} {request.url.path} "
        f"\nException details: {repr(exc)}"
    )

    # Отдаем клиенту безопасный стандартизированный ответ
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Внутренняя ошибка базы данных. Пожалуйста, обратитесь в техническую поддержку."
        },
    )


def setup_exception_handlers(app: FastAPI):
    app.add_exception_handler(TaskDoesNotExistsError, not_found_exception_handler)
    app.add_exception_handler(TeamDoesNotExistsError, not_found_exception_handler)
    app.add_exception_handler(RoleDoesNotExistsError, internal_server_exception_handler)
    app.add_exception_handler(AccessDeniedError, access_denied_exception_handler)
    app.add_exception_handler(UserNotActiveError, access_denied_exception_handler)
    app.add_exception_handler(TeamAlreadyExistsError, bad_request_exception_handler)
    app.add_exception_handler(UserAlreadyInTeamError, bad_request_exception_handler)
    app.add_exception_handler(UserDoesNotExistsError, bad_request_exception_handler)
    app.add_exception_handler(UserExistsError, bad_request_exception_handler)
    app.add_exception_handler(UserAlreadyActiveError, conflict_exception_handler)
    app.add_exception_handler(BadCredentialsError, not_authorized_exception_handler)
    app.add_exception_handler(PasswordsMismatchError, bad_request_exception_handler)
    app.add_exception_handler(TaskDoesNotCompletedError, bad_request_exception_handler)
    app.add_exception_handler(TaskAlreadyEvaluatedError, bad_request_exception_handler)
    app.add_exception_handler(MeetingOverlapError, conflict_exception_handler)
    app.add_exception_handler(MeetingDoesNotExistsError, not_found_exception_handler)
    app.add_exception_handler(DatetimeCompatibleError, bad_request_exception_handler)
    app.add_exception_handler(
        UnknownAccessLevelError, internal_server_exception_handler
    )
    app.add_exception_handler(InvalidPasswordError, access_denied_exception_handler)
    app.add_exception_handler(CommentDoesNotExistsError, not_found_exception_handler)
    app.add_exception_handler(EvaluationDoesNotExistsError, not_found_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
