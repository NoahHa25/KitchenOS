from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


MemoryType = Literal[
    "equipment",
    "supplier",
    "inventory",
    "sales",
    "waste",
    "operational",
    "recipe",
    "staff",
    "financial",
    "other",
]

MemoryImportance = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class RestaurantMemoryCreate(BaseModel):
    memory_type: MemoryType
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    importance: MemoryImportance = "medium"
    tags: str | None = None


class RestaurantMemoryUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    description: str | None = Field(
        default=None,
        min_length=1,
    )
    importance: MemoryImportance | None = None
    tags: str | None = None
    resolved_at: datetime | None = None


class RestaurantMemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    memory_type: MemoryType
    title: str
    description: str
    importance: MemoryImportance
    tags: str | None
    created_at: datetime
    resolved_at: datetime | None