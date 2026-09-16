from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IngredientCreate(BaseModel):
    restaurant_id: UUID
    name: str
    unit: str
    current_stock: float = 0
    minimum_stock: float = 0
    cost_per_unit: float = 0


class IngredientUpdate(BaseModel):
    name: str | None = None
    unit: str | None = None
    current_stock: float | None = None
    minimum_stock: float | None = None
    cost_per_unit: float | None = None


class IngredientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    name: str
    unit: str
    current_stock: float
    minimum_stock: float
    cost_per_unit: float
    created_at: datetime
    updated_at: datetime