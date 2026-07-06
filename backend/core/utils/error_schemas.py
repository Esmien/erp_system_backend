from pydantic import BaseModel


class ErrorResponseSchema(BaseModel):
    detail: str
    status_code: int
