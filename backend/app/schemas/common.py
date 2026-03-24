from pydantic import BaseModel, ConfigDict, Field
from typing import Generic, TypeVar, Any

T = TypeVar("T")


def to_camel(string: str) -> str:
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class ApiResponse(CamelModel, Generic[T]):
    """표준 API 응답 래퍼"""
    status: str = "success"
    data: T | None = None
    message: str | None = None


class ApiError(CamelModel):
    """RFC 7807 Problem Details 형식 에러 응답"""
    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None


class OffsetPagination(CamelModel):
    """오프셋 기반 페이지네이션"""
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(CamelModel, Generic[T]):
    """페이지네이션 포함 응답"""
    status: str = "success"
    data: list[T]
    pagination: OffsetPagination


class CursorPagination(CamelModel):
    """커서 기반 페이지네이션"""
    next_cursor: str | None = None
    prev_cursor: str | None = None
    has_next: bool = False
    limit: int = 20
