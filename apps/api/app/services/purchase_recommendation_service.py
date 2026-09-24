from app.services.ingredient_service import IngredientService


class PurchaseRecommendationService:
    def __init__(
        self,
        ingredient_service: IngredientService,
    ):
        self.ingredient_service = ingredient_service

    async def get_purchase_recommendations(
        self,
        restaurant_id,
    ):
        low_stock = await self.ingredient_service.get_low_stock(
            restaurant_id,
        )

        recommendations = []

        for ingredient in low_stock:
            amount_needed = (
                ingredient.minimum_stock
                - ingredient.current_stock
            )

            recommendations.append(
                {
                    "ingredient_id": ingredient.id,
                    "ingredient_name": ingredient.name,
                    "current_stock": ingredient.current_stock,
                    "minimum_stock": ingredient.minimum_stock,
                    "recommended_purchase": amount_needed,
                    "unit": ingredient.unit,
                }
            )

        return recommendations
