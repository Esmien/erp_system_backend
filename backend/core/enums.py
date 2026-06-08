from enum import StrEnum

TASK_NOT_FOUND = "Задача не найдена."


class RoleName(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class BusinessElementName(StrEnum):
    TEAMS = "teams"
    TASKS = "tasks"
    COMMENTS = "comments"
    USERS = "users"
    EVALUATIONS = "evaluations"
    MEETINGS = "meetings"


class Action(StrEnum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    CHANGE_STATUS = "change_status"


class AccessLevel(StrEnum):
    ALL = "all"
    AUTHOR = "author"
    PARTICIPANT = "participant"


class TaskStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class MeetingStatus(StrEnum):
    PENDING = "pending"
    IN_PROCESS = "in_process"
    ENDS = "ends"
    CANCELED = "canceled"
