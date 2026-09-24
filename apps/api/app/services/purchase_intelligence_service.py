from uuid import UUID

from app.services.ingredient_service import IngredientService
from app.services.purchase_recommendation_service import (
    PurchaseRecommendationService,
)
from app.services.recipe_impact_service import RecipeImpactService
from app.services.sales_intelligence_service import (
    SalesIntelligenceService,
)


class PurchaseIntelligenceService:
    def __init__(
        self,
        ingredient_service: IngredientService,
        purchase_recommendation_service: PurchaseRecommendationService,
        recipe_impact_service: RecipeImpactService,
        sales_intelligence_service: SalesIntelligenceService,
    ):
        self.ingredient_service = ingredient_service
        self.purchase_recommendation_service = (
            purchase_recommendation_service
        )
        self.recipe_impact_service = recipe_impact_service
        self.sales_intelligence_service = sales_intelligence_service

    async def get_purchase_reason(
        self,
        restaurant_id: UUID,
        ingredient_name: str,
    ) -> dict | None:
        ingredient = (
            await self.ingredient_service.find_ingredient_by_name(
                restaurant_id=restaurant_id,
                query=ingredient_name,
            )
        )

        if ingredient is None:
            return None

        recommendations = (
            await self.purchase_recommendation_service
            .get_purchase_recommendations(
                restaurant_id=restaurant_id,
            )
        )

        recommendation = next(
            (
                item
                for item in recommendations
                if item["ingredient_id"] == ingredient.id
            ),
            None,
        )

        if recommendation is None:
            return {
                "ingredient_id": ingredient.id,
                "ingredient_name": ingredient.name,
                "current_stock": ingredient.current_stock,
                "minimum_stock": ingredient.minimum_stock,
                "recommended_purchase": 0,
                "unit": ingredient.unit,
                "affected_recipes": [],
            }

        affected_recipes = (
            await self.recipe_impact_service
            .get_low_stock_recipe_impact(
                restaurant_id=restaurant_id,
            )
        )

        sales = (
            await self.sales_intelligence_service
            .get_top_selling_recipes(
                restaurant_id=restaurant_id,
            )
        )

        sales_by_recipe_id = {
            item["recipe_id"]: item["quantity_sold"]
            for item in sales
        }

        ingredient_id = ingredient.id

        related_recipes = []

        for recipe in affected_recipes:
            affected_ingredients = recipe[
                "affected_ingredients"
            ]

            uses_ingredient = any(
                item["ingredient_id"] == ingredient_id
                for item in affected_ingredients
            )

            if not uses_ingredient:
                continue

            related_recipes.append(
                {
                    "recipe_id": recipe["recipe_id"],
                    "recipe_name": recipe["recipe_name"],
                    "quantity_sold": sales_by_recipe_id.get(
                        recipe["recipe_id"],
                        0,
                    ),
                }
            )

        related_recipes.sort(
            key=lambda item: item["quantity_sold"],
            reverse=True,
        )

        return {
            "ingredient_id": ingredient.id,
            "ingredient_name": ingredient.name,
            "current_stock": recommendation["current_stock"],
            "minimum_stock": recommendation["minimum_stock"],
            "recommended_purchase": (
                recommendation["recommended_purchase"]
            ),
            "unit": recommendation["unit"],
            "affected_recipes": related_recipes,
        }