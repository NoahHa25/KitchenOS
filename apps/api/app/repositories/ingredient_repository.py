from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingredient import Ingredient


class IngredientRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        restaurant_id: UUID,
        name: str,
        unit: str,
        current_stock: float,
        minimum_stock: float,
        cost_per_unit: float,
    ) -> Ingredient:
        ingredient = Ingredient(
            restaurant_id=restaurant_id,
            name=name,
            unit=unit,
            current_stock=current_stock,
            minimum_stock=minimum_stock,
            cost_per_unit=cost_per_unit,
        )

        self.db.add(ingredient)
        await self.db.flush()

        return ingredient

    async def get_all(
        self,
        restaurant_id: UUID,
    ) -> list[Ingredient]:
        result = await self.db.execute(
            select(Ingredient).where(
                Ingredient.restaurant_id == restaurant_id
            )
        )

        return list(result.scalars().all())

    async def get_by_id(
        self,
        restaurant_id: UUID,
        ingredient_id: UUID,
    ) -> Ingredient | None:
        result = await self.db.execute(
            select(Ingredient).where(
                Ingredient.id == ingredient_id,
                Ingredient.restaurant_id == restaurant_id,
            )
        )

        return result.scalar_one_or_none()

    async def update(
        self,
        restaurant_id: UUID,
        ingredient_id: UUID,
        name: str | None = None,
        unit: str | None = None,
        current_stock: float | None = None,
        minimum_stock: float | None = None,
        cost_per_unit: float | None = None,
    ) -> Ingredient | None:
        ingredient = await self.get_by_id(
            restaurant_id=restaurant_id,
            ingredient_id=ingredient_id,
        )

        if ingredient is None:
            return None

        if name is not None:
            ingredient.name = name

        if unit is not None:
            ingredient.unit = unit

        if current_stock is not None:
            ingredient.current_stock = current_stock

        if minimum_stock is not None:
            ingredient.minimum_stock = minimum_stock

        if cost_per_unit is not None:
            ingredient.cost_per_unit = cost_per_unit

        await self.db.flush()

        return ingredient

    async def delete(
        self,
        restaurant_id: UUID,
        ingredient_id: UUID,
    ) -> bool:
        ingredient = await self.get_by_id(
            restaurant_id=restaurant_id,
            ingredient_id=ingredient_id,
        )

        if ingredient is None:
            return False

        await self.db.delete(ingredient)
        await self.db.flush()

        return True

    async def get_low_stock(
        self,
        restaurant_id: UUID,
    ) -> list[Ingredient]:
        result = await self.db.execute(
            select(Ingredient).where(
                Ingredient.restaurant_id == restaurant_id,
                Ingredient.current_stock
                <= Ingredient.minimum_stock,
            )
        )

        return list(result.scalars().all())