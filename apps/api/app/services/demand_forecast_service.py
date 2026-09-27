from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from app.repositories.order_repository import OrderRepository
from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)
from app.repositories.recipe_repository import RecipeRepository
from app.services.ingredient_service import IngredientService


class DemandForecastService:
    def __init__(
        self,
        order_repository: OrderRepository,
        recipe_repository: RecipeRepository,
        recipe_ingredient_repository: RecipeIngredientRepository,
        ingredient_service: IngredientService,
    ):
        self.order_repository = order_repository
        self.recipe_repository = recipe_repository
        self.recipe_ingredient_repository = (
            recipe_ingredient_repository
        )
        self.ingredient_service = ingredient_service

    async def get_forecast(
        self,
        restaurant_id: UUID,
        ingredient_name: str,
        forecast_days: int = 7,
        safety_stock: Decimal = Decimal("0"),
        lookback_days: int = 30,
    ) -> dict | None:
        ingredient = (
            await self.ingredient_service.find_ingredient_by_name(
                restaurant_id=restaurant_id,
                query=ingredient_name,
            )
        )

        if ingredient is None:
            return None

        completed_orders = (
            await self.order_repository.get_completed_orders(
                restaurant_id,
            )
        )

        now = datetime.now(timezone.utc)

        lookback_start = (
            now
            - timedelta(days=lookback_days)
            - timedelta(seconds=1)
        )

        total_usage = Decimal("0")

        for order in completed_orders:
            order_created_at = order.created_at

            if order_created_at.tzinfo is None:
                order_created_at = order_created_at.replace(
                    tzinfo=timezone.utc,
                )

            if order_created_at < lookback_start:
                continue

            for order_item in order.items:
                recipe = await self.recipe_repository.get_by_id(
                    restaurant_id,
                    order_item.recipe_id,
                )

                if recipe is None:
                    continue

                recipe_ingredients = (
                    await self.recipe_ingredient_repository.get_by_recipe(
                        recipe_id=recipe.id,
                    )
                )

                for recipe_ingredient in recipe_ingredients:
                    if (
                        recipe_ingredient.ingredient_id
                        != ingredient.id
                    ):
                        continue

                    order_quantity = Decimal(
                        str(order_item.quantity)
                    )

                    ingredient_quantity = Decimal(
                        str(recipe_ingredient.quantity)
                    )

                    total_usage += (
                        order_quantity
                        * ingredient_quantity
                    )

        average_daily_usage = (
            total_usage
            / Decimal(str(lookback_days))
        )

        forecasted_usage = (
            average_daily_usage
            * Decimal(str(forecast_days))
        )

        current_stock = Decimal(
            str(ingredient.current_stock)
        )

        safety_stock = Decimal(
            str(safety_stock)
        )

        suggested_purchase = max(
            Decimal("0"),
            forecasted_usage
            + safety_stock
            - current_stock,
        )

        return {
            "ingredient_id": ingredient.id,
            "ingredient_name": ingredient.name,
            "current_stock": current_stock,
            "unit": ingredient.unit,
            "average_daily_usage": average_daily_usage,
            "forecast_days": forecast_days,
            "forecasted_usage": forecasted_usage,
            "safety_stock": safety_stock,
            "suggested_purchase": suggested_purchase,
        }