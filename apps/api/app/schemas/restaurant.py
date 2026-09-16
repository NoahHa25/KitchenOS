from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RestaurantCreate(BaseModel):
    name: str
    slug: str


class RestaurantUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None

class RestaurantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime