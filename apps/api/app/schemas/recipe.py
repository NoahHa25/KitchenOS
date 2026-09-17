from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecipeCreate(BaseModel):
    restaurant_id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(
        default=None,
        max_length=500,
    )


class RecipeUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=500,
    )


class RecipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime