from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException

from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.inventory_movement_repository import (
    InventoryMovementRepository,
)
from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)


class InventoryConsumptionService:
    def __init__(
        self,
        ingredient_repository: IngredientRepository,
        recipe_ingredient_repository: RecipeIngredientRepository,
        inventory_movement_repository: InventoryMovementRepository,
    ):
        self.ingredient_repository = ingredient_repository
        self.recipe_ingredient_repository = (
            recipe_ingredient_repository
        )
        self.inventory_movement_repository = (
            inventory_movement_repository
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

        recipe_quantity = Decimal(str(recipe_quantity))

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

            ingredient_quantity = Decimal(
                str(recipe_ingredient.quantity)
            )

            required_quantity = (
                ingredient_quantity * recipe_quantity
            )

            required.append(
                {
                    "ingredient": ingredient,
                    "required_quantity": required_quantity,
                }
            )

        return required

    @staticmethod
    def aggregate_required_ingredients(
        required: list[dict],
    ) -> list[dict]:
        aggregated: dict[UUID, dict] = {}

        for item in required:
            ingredient = item["ingredient"]
            required_quantity = Decimal(
                str(item["required_quantity"])
            )

            if ingredient.id not in aggregated:
                aggregated[ingredient.id] = {
                    "ingredient": ingredient,
                    "required_quantity": required_quantity,
                }
            else:
                aggregated[ingredient.id][
                    "required_quantity"
                ] += required_quantity

        return list(aggregated.values())

    async def validate_stock(
        self,
        required: list[dict],
    ) -> None:
        for item in required:
            ingredient = item["ingredient"]
            required_quantity = Decimal(
                str(item["required_quantity"])
            )
            current_stock = Decimal(
                str(ingredient.current_stock)
            )

            if current_stock < required_quantity:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Insufficient stock for "
                        f"{ingredient.name}"
                    ),
                )

    async def consume_stock(
        self,
        required: list[dict],
        order_id: UUID,
    ) -> None:
        for item in required:
            ingredient = item["ingredient"]
            required_quantity = Decimal(
                str(item["required_quantity"])
            )

            current_stock = Decimal(
                str(ingredient.current_stock)
            )

            ingredient.current_stock = (
                current_stock - required_quantity
            )

            await self.inventory_movement_repository.create(
                ingredient_id=ingredient.id,
                movement_type="usage",
                quantity=required_quantity,
                unit_cost=Decimal(
                    str(ingredient.cost_per_unit)
             ),
             reason=f"Order {order_id}",
     )

