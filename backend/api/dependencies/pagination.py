import math
from collections.abc import Sequence
from typing import Annotated, TypeVar

from fastapi import Depends, Query
from pydantic import BaseModel

T = TypeVar("T")


class Page[T](BaseModel):
    """Универсальная схема для возврата пагинированных данных."""

    items: Sequence[T]
    total: int
    page: int
    size: int
    total_pages: int

    @classmethod
    def create(cls, items: Sequence[T], total: int, params: "PaginationParams") -> "Page[T]":
        """Фабричный метод для автоматической сборки пагинированного ответа"""
        total_pages = math.ceil(total / params.size) if total > 0 else 1
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            total_pages=total_pages,
        )


class PaginationParams:
    """Класс-зависимость для парсинга параметров запроса."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Номер страницы"),
        size: int = Query(default=20, ge=1, le=100, description="Количество элементов на странице"),
    ):
        self.page = page
        self.size = size
        self.limit = size
        self.offset = (page - 1) * size


PaginationParamsDepends = Annotated[PaginationParams, Depends()]
