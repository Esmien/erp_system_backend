from enum import StrEnum


class RoleName(StrEnum):
    USER = "user"
    ADMIN = "admin"
    MANAGER = "manager"


class BusinessElementName(StrEnum):
    TEAMS = "teams"
    TASKS = "tasks"


class PermissionName(StrEnum):
    READ = "read_permission"
    READ_ALL = "read_all_permission"
    CREATE = "create_permission"
    UPDATE = "update_permission"
    UPDATE_ALL = "update_all_permission"
    DELETE = "delete_permission"
    DELETE_ALL = "delete_all_permission"


class TaskStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
