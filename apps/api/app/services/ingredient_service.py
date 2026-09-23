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
        ingredient = await self.repository.create(
            restaurant_id=data.restaurant_id,
            name=data.name,
            unit=data.unit,
            current_stock=data.current_stock,
            minimum_stock=data.minimum_stock,
            cost_per_unit=data.cost_per_unit,
        )

        await self.repository.db.commit()
        await self.repository.db.refresh(ingredient)

        return ingredient

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
        ingredient = await self.repository.update(
            restaurant_id=restaurant_id,
            ingredient_id=ingredient_id,
            **data.model_dump(exclude_unset=True),
        )

        if ingredient is None:
            return None

        await self.repository.db.commit()
        await self.repository.db.refresh(ingredient)

        return ingredient

    async def delete_ingredient(
        self,
        restaurant_id: UUID,
        ingredient_id: UUID,
    ):
        deleted = await self.repository.delete(
            restaurant_id=restaurant_id,
            ingredient_id=ingredient_id,
        )

        if not deleted:
            return False

        await self.repository.db.commit()

        return True

    async def get_low_stock(
        self,
        restaurant_id: UUID,
    ):
        return await self.repository.get_low_stock(
            restaurant_id=restaurant_id,
        )

    async def find_ingredient_by_name(
        self,
        restaurant_id: UUID,
        query: str,
    ):
        return await self.repository.find_by_name(
            restaurant_id=restaurant_id,
            query=query,
        )
