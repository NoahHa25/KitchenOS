from uuid import UUID

from pydantic import BaseModel


class SalesSummary(BaseModel):
    total_orders: int
    total_revenue: float


class LowStockItem(BaseModel):
    ingredient_id: UUID
    ingredient_name: str
    current_stock: float
    minimum_stock: float
    unit: str


class AffectedIngredient(BaseModel):
    ingredient_id: UUID
    ingredient_name: str
    current_stock: float
    minimum_stock: float
    unit: str
    required_quantity: float


class RecipeImpactItem(BaseModel):
    recipe_id: UUID
    recipe_name: str
    affected_ingredients: list[AffectedIngredient]


class PurchaseRecommendation(BaseModel):
    ingredient_id: UUID
    ingredient_name: str
    current_stock: float
    minimum_stock: float
    recommended_purchase: float
    unit: str


class TopRecipe(BaseModel):
    recipe_id: UUID
    recipe_name: str
    quantity_sold: int


class DemandForecast(BaseModel):
    ingredient_id: UUID
    ingredient_name: str
    current_stock: float
    unit: str
    average_daily_usage: float
    forecast_days: int
    forecasted_usage: float
    safety_stock: float
    suggested_purchase: float


class MorningBriefResponse(BaseModel):
    sales: SalesSummary
    low_stock: list[LowStockItem]
    recipe_impact: list[RecipeImpactItem]
    purchase_recommendations: list[PurchaseRecommendation]
    top_recipe: TopRecipe | None
    demand_forecast: list[DemandForecast]