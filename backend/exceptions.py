class UserExistsError(Exception):
    pass


class UserDoesNotExistsError(Exception):
    pass


class RoleDoesNotExistsError(Exception):
    pass


class InvalidPasswordError(Exception):
    pass


class UserNotActiveError(Exception):
    pass


class TeamDoesNotExistsError(Exception):
    pass


class AccessDeniedError(Exception):
    pass


class TeamAlreadyExistsError(Exception):
    pass


class UserAlreadyInTeamError(Exception):
    pass


class UserAlreadyActiveError(Exception):
    pass


class TaskDoesNotExistsError(Exception):
    pass


class TaskAlreadyEvaluatedError(Exception):
    pass


class TaskDoesNotCompletedError(Exception):
    pass


class EvaluationDoesNotExistsError(Exception):
    pass


class BadCredentialsError(Exception):
    pass


class PasswordsMismatchError(Exception):
    pass


class MeetingOverlapError(Exception):
    pass


class MeetingDoesNotExistsError(Exception):
    pass


class DatetimeCompatibleError(Exception):
    pass
