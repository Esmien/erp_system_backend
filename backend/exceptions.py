class UserExistsError(Exception):
    pass  # handled


class UserDoesNotExistsError(Exception):
    pass  # handled


class RoleDoesNotExistsError(Exception):
    pass  # handled


class InvalidPasswordError(Exception):
    pass  # handled


class UserNotActiveError(Exception):
    pass  # handled


class TeamDoesNotExistsError(Exception):
    pass  # handled


class AccessDeniedError(Exception):
    pass  # handled


class UnknownAccessLevelError(Exception):
    pass  # handled


class TeamAlreadyExistsError(Exception):
    pass  # handled


class UserAlreadyInTeamError(Exception):
    pass  # handled


class UserAlreadyActiveError(Exception):
    pass  # handled


class TaskDoesNotExistsError(Exception):
    pass  # handled


class TaskAlreadyEvaluatedError(Exception):
    pass  # handled


class TaskDoesNotCompletedError(Exception):
    pass  # handled


class BadCredentialsError(Exception):
    pass  # handled


class PasswordsMismatchError(Exception):
    pass  # handled


class MeetingOverlapError(Exception):
    pass  # handled


class MeetingDoesNotExistsError(Exception):
    pass  # handled


class DatetimeCompatibleError(Exception):
    pass  # handled


class CommentDoesNotExistsError(Exception):
    pass  # handled


class EvaluationDoesNotExistsError(Exception):
    pass  # handled
