from decimal import Decimal
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

        recipe_ingredients = await self.recipe_ingredient_repository.get_by_recipe(
            recipe_id=recipe_id,
        )

        total_cost = Decimal("0")
        breakdown = []

        for recipe_item in recipe_ingredients:
            ingredient = await self.ingredient_repository.get_by_id(
                restaurant_id=restaurant_id,
                ingredient_id=recipe_item.ingredient_id,
            )

            if ingredient is None:
                continue

            quantity = Decimal(str(recipe_item.quantity))
            unit_cost = Decimal(str(ingredient.cost_per_unit))

            item_cost = quantity * unit_cost
            total_cost += item_cost

            breakdown.append(
                {
                    "ingredient": ingredient.name,
                    "quantity": float(quantity),
                    "unit": ingredient.unit,
                    "cost_per_unit": float(unit_cost),
                    "cost": float(item_cost),
                }
            )

        return {
            "recipe_id": recipe.id,
            "recipe_name": recipe.name,
            "food_cost": float(total_cost),
            "breakdown": breakdown,
        }