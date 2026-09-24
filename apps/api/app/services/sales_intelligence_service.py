from collections import defaultdict
from uuid import UUID

from app.repositories.order_repository import OrderRepository
from app.repositories.recipe_repository import RecipeRepository


class SalesIntelligenceService:
    def __init__(
        self,
        order_repository: OrderRepository,
        recipe_repository: RecipeRepository,
    ):
        self.order_repository = order_repository
        self.recipe_repository = recipe_repository

    async def get_top_selling_recipes(
        self,
        restaurant_id: UUID,
    ) -> list[dict]:
        completed_orders = (
            await self.order_repository.get_completed_orders(
                restaurant_id,
            )
        )

        sales = defaultdict(
            lambda: {
                "recipe_id": None,
                "quantity_sold": 0,
            }
        )

        for order in completed_orders:
            for item in order.items:
                recipe_id = item.recipe_id

                sales[recipe_id]["recipe_id"] = recipe_id
                sales[recipe_id]["quantity_sold"] += item.quantity

        recommendations = []

        for recipe_id, sale in sales.items():
            recipe = await self.recipe_repository.get_by_id(
                restaurant_id,
                recipe_id,
            )

            if recipe is None:
                continue

            recommendations.append(
                {
                    "recipe_id": recipe_id,
                    "recipe_name": recipe.name,
                    "quantity_sold": sale["quantity_sold"],
                }
            )

        recommendations.sort(
            key=lambda item: item["quantity_sold"],
            reverse=True,
        )

        return recommendations