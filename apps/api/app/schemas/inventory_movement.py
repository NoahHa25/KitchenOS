from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class InventoryMovementCreate(BaseModel):
    ingredient_id: UUID
    movement_type: str
    quantity: float
    reason: str | None = None


class InventoryMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingredient_id: UUID
    movement_type: str
    quantity: float
    reason: str | None
    created_at: datetime