from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException

from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)


class InventoryConsumptionService:
    def __init__(
        self,
        ingredient_repository: IngredientRepository,
        recipe_ingredient_repository: RecipeIngredientRepository,
    ):
        self.ingredient_repository = ingredient_repository
        self.recipe_ingredient_repository = (
            recipe_ingredient_repository
        )

    async def calculate_required_ingredients(
        self,
        restaurant_id: UUID,
        recipe_id: UUID,
        recipe_quantity: Decimal,
    ) -> list[dict]:
        recipe_ingredients = (
            await self.recipe_ingredient_repository.get_by_recipe(
                recipe_id=recipe_id,
            )
        )

        required = []

        for recipe_ingredient in recipe_ingredients:
            ingredient = await self.ingredient_repository.get_by_id(
                restaurant_id=restaurant_id,
                ingredient_id=recipe_ingredient.ingredient_id,
            )

            if ingredient is None:
                raise HTTPException(
                    status_code=404,
                    detail="Ingredient not found",
                )

            required_quantity = (
                recipe_ingredient.quantity
                * recipe_quantity
            )

            required.append(
                {
                    "ingredient": ingredient,
                    "required_quantity": required_quantity,
                }
            )

        return required

    async def validate_stock(
        self,
        required: list[dict],
    ) -> None:
        for item in required:
            ingredient = item["ingredient"]
            required_quantity = item["required_quantity"]

            if ingredient.current_stock < required_quantity:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Insufficient stock for "
                        f"{ingredient.name}"
                    ),
                )