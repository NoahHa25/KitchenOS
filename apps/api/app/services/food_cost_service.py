from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)
from app.repositories.recipe_repository import RecipeRepository


class FoodCostService:
    def __init__(
        self,
        recipe_repository: RecipeRepository,
        recipe_ingredient_repository: RecipeIngredientRepository,
        ingredient_repository: IngredientRepository,
    ):
        self.recipe_repository = recipe_repository
        self.recipe_ingredient_repository = recipe_ingredient_repository
        self.ingredient_repository = ingredient_repository

    async def calculate_food_cost(
        self,
        restaurant_id: UUID,
        recipe_id: UUID,
    ):
        recipe = await self.recipe_repository.get_by_id(
            restaurant_id=restaurant_id,
            recipe_id=recipe_id,
        )

        if recipe is None:
            return None

        recipe_ingredients = (
            await self.recipe_ingredient_repository.get_by_recipe(
                recipe_id=recipe_id,
            )
        )

        total_food_cost = Decimal("0.00")
        breakdown = []

        for recipe_ingredient in recipe_ingredients:
            ingredient = await self.ingredient_repository.get_by_id(
                restaurant_id=restaurant_id,
                ingredient_id=recipe_ingredient.ingredient_id,
            )

            if ingredient is None:
                continue

            quantity = Decimal(str(recipe_ingredient.quantity))
            cost_per_unit = Decimal(str(ingredient.cost_per_unit))

            total_cost = (
                quantity * cost_per_unit
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

            total_food_cost += total_cost

            breakdown.append(
                {
                    "ingredient": ingredient.name,
                    "quantity": quantity,
                    "cost_per_unit": cost_per_unit,
                    "total_cost": total_cost,
                }
            )

        total_food_cost = total_food_cost.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        return {
            "recipe_id": recipe.id,
            "recipe_name": recipe.name,
            "food_cost": total_food_cost,
            "breakdown": breakdown,
        }

