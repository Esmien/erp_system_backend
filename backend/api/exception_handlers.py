from fastapi import Request, status, FastAPI
from fastapi.responses import JSONResponse

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
    BadCredentialsError, PasswordsMismatchError,
)


def not_found_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


def internal_server_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
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
