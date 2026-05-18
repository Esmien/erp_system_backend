class UserExistsError(Exception):
    pass


class UserDoesNotExistsError(Exception):
    pass


class RoleDoesNotExistsError(Exception):
    pass


class InvalidPasswordError(Exception):
    pass
