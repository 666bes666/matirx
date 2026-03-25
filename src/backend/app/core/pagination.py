from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


@dataclass
class PaginationParams:
    page: int = Query(default=1, ge=1)
    per_page: int = Query(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int


async def paginate(
    db: AsyncSession,
    query: Select,
    params: PaginationParams,
    schema: type[Any],
) -> PaginatedResponse:
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(query.offset(params.offset).limit(params.per_page))
    items = result.scalars().all()

    return PaginatedResponse(
        items=[schema.model_validate(item) for item in items],
        total=total,
        page=params.page,
        per_page=params.per_page,
    )
