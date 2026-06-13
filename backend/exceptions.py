class UserExistsError(Exception): ...  # handled


class UserDoesNotExistError(Exception): ...  # handled


class RoleDoesNotExistError(Exception): ...  # handled


class InvalidPasswordError(Exception): ...  # handled


class UserNotActiveError(Exception): ...  # handled


class TeamDoesNotExistError(Exception): ...  # handled


class AccessDeniedError(Exception): ...  # handled


class UnknownAccessLevelError(Exception): ...  # handled


class TeamAlreadyExistError(Exception): ...  # handled


class UserAlreadyInTeamError(Exception): ...  # handled


class UserAlreadyActiveError(Exception): ...  # handled


class TaskDoesNotExistError(Exception): ...  # handled


class TaskAlreadyEvaluatedError(Exception): ...  # handled


class TaskNotCompletedError(Exception): ...  # handled


class BadCredentialsError(Exception): ...  # handled


class PasswordsMismatchError(Exception): ...  # handled


class MeetingOverlapError(Exception): ...  # handled


class MeetingDoesNotExistError(Exception): ...  # handled


class DatetimeMismatchError(Exception): ...  # handled


class CommentDoesNotExistsError(Exception): ...  # handled


class EvaluationDoesNotExistError(Exception): ...  # handled
