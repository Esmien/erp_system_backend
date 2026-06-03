class UserExistsError(Exception):  # handled
    pass


class UserDoesNotExistsError(Exception):  # handled
    pass


class RoleDoesNotExistsError(Exception):  # handled
    pass


class InvalidPasswordError(Exception):
    pass


class UserNotActiveError(Exception):  # handled
    pass


class TeamDoesNotExistsError(Exception):  # handled
    pass


class AccessDeniedError(Exception):  # handled
    pass


class TeamAlreadyExistsError(Exception):  # handled
    pass


class UserAlreadyInTeamError(Exception):  # handled
    pass


class UserAlreadyActiveError(Exception):  # handled
    pass


class TaskDoesNotExistsError(Exception):  # handled
    pass


class TaskAlreadyEvaluatedError(Exception):  # handled
    pass


class TaskDoesNotCompletedError(Exception):  # handled
    pass


class BadCredentialsError(Exception):  # handled
    pass


class PasswordsMismatchError(Exception):  # handled
    pass


class MeetingOverlapError(Exception):  # handled
    pass


class MeetingDoesNotExistsError(Exception):  # handled
    pass


class DatetimeCompatibleError(Exception):  # handled
    pass
