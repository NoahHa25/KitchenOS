from uuid import UUID

from pydantic import BaseModel

class FoodCostBreakdownItem(BaseModel):
    ingredient: str
    quantity: float
    cost_per_unit: float
    total_cost: float

class FoodCostResponse(BaseModel):
    recipe_id: UUID
    recipe_name: str
    food_cost: float
    breakdown: list[FoodCostBreakdownItem]
