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
