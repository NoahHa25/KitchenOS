from uuid import UUID

from app.repositories.ingredient_repository import IngredientRepository
from app.schemas.ingredient import IngredientCreate, IngredientUpdate


class IngredientService:
    def __init__(self, repository: IngredientRepository):
        self.repository = repository

    async def create_ingredient(
        self,
        data: IngredientCreate,
    ):
        return await self.repository.create(
            restaurant_id=data.restaurant_id,
            name=data.name,
            unit=data.unit,
            current_stock=data.current_stock,
            minimum_stock=data.minimum_stock,
            cost_per_unit=data.cost_per_unit,
        )

    async def list_ingredients(
        self,
        restaurant_id: UUID,
    ):
        return await self.repository.get_all(
            restaurant_id=restaurant_id,
        )

    async def get_ingredient(
        self,
        restaurant_id: UUID,
        ingredient_id: UUID,
    ):
        return await self.repository.get_by_id(
            restaurant_id=restaurant_id,
            ingredient_id=ingredient_id,
        )

    async def update_ingredient(
        self,
        restaurant_id: UUID,
        ingredient_id: UUID,
        data: IngredientUpdate,
    ):
        return await self.repository.update(
            restaurant_id=restaurant_id,
            ingredient_id=ingredient_id,
            name=data.name,
            unit=data.unit,
            current_stock=data.current_stock,
            minimum_stock=data.minimum_stock,
            cost_per_unit=data.cost_per_unit,
        )

    async def delete_ingredient(
        self,
        restaurant_id: UUID,
        ingredient_id: UUID,
    ):
        return await self.repository.delete(
            restaurant_id=restaurant_id,
            ingredient_id=ingredient_id,
        )