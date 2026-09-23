from uuid import UUID

from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)
from app.repositories.recipe_repository import RecipeRepository
from app.services.ingredient_service import IngredientService


class RecipeImpactService:
    def __init__(
        self,
        recipe_repository: RecipeRepository,
        recipe_ingredient_repository: RecipeIngredientRepository,
        ingredient_service: IngredientService,
    ):
        self.recipe_repository = recipe_repository
        self.recipe_ingredient_repository = recipe_ingredient_repository
        self.ingredient_service = ingredient_service

    async def get_low_stock_recipe_impact(
        self,
        restaurant_id: UUID,
    ) -> list[dict]:
        low_stock_ingredients = (
            await self.ingredient_service.get_low_stock(
                restaurant_id=restaurant_id,
            )
        )

        if not low_stock_ingredients:
            return []

        low_stock_ids = {
            ingredient.id
            for ingredient in low_stock_ingredients
        }

        recipes = await self.recipe_repository.get_all(
            restaurant_id=restaurant_id,
        )

        affected_recipes = []

        for recipe in recipes:
            recipe_ingredients = (
                await self.recipe_ingredient_repository.get_by_recipe(
                    recipe_id=recipe.id,
                )
            )

            affected_ingredients = []

            for item in recipe_ingredients:
                if item.ingredient_id not in low_stock_ids:
                    continue

                ingredient = item.ingredient

                affected_ingredients.append(
                    {
                        "ingredient_id": ingredient.id,
                        "ingredient_name": ingredient.name,
                        "current_stock": ingredient.current_stock,
                        "minimum_stock": ingredient.minimum_stock,
                        "unit": ingredient.unit,
                        "required_quantity": item.quantity,
                    }
                )

            if affected_ingredients:
                affected_recipes.append(
                    {
                        "recipe_id": recipe.id,
                        "recipe_name": recipe.name,
                        "affected_ingredients": affected_ingredients,
                    }
                )

        return affected_recipes