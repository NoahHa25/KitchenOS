from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InventoryMovementCreate(BaseModel):
    ingredient_id: UUID
    movement_type: str
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal | None = Field(
        default=None,
        ge=0,
    )
    reason: str | None = None


class InventoryMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ingredient_id: UUID
    movement_type: str
    quantity: Decimal
    unit_cost: Decimal
    reason: str | None
    created_at: datetime

