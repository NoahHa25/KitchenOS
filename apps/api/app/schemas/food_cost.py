from uuid import UUID

from pydantic import BaseModel


class FoodCostBreakdown(BaseModel):
    ingredient: str
    quantity: float
    unit: str
    cost_per_unit: float
    cost: float


class FoodCostResponse(BaseModel):
    recipe_id: UUID
    recipe_name: str
    food_cost: float
    breakdown: list[FoodCostBreakdown]