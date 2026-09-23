from uuid import UUID

from sqlalchemy import func, select
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
        current_stock,
        minimum_stock,
        cost_per_unit,
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
            select(Ingredient)
            .where(
                Ingredient.restaurant_id == restaurant_id,
            )
            .order_by(
                Ingredient.name.asc(),
            )
        )

        return list(result.scalars().all())

    async def get_by_id(
        self,
        restaurant_id: UUID,
        ingredient_id: UUID,
    ) -> Ingredient | None:
        result = await self.db.execute(
            select(Ingredient)
            .where(
                Ingredient.id == ingredient_id,
                Ingredient.restaurant_id == restaurant_id,
            )
        )

        return result.scalar_one_or_none()

    async def update(
        self,
        restaurant_id: UUID,
        ingredient_id: UUID,
        **values,
    ) -> Ingredient | None:
        ingredient = await self.get_by_id(
            restaurant_id=restaurant_id,
            ingredient_id=ingredient_id,
        )

        if ingredient is None:
            return None

        for field, value in values.items():
            if value is not None:
                setattr(ingredient, field, value)

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

    async def find_by_name(
        self,
        restaurant_id: UUID,
        query: str,
    ) -> Ingredient | None:
        normalized_query = query.strip().lower()

        result = await self.db.execute(
            select(Ingredient)
            .where(
                Ingredient.restaurant_id == restaurant_id,
                func.lower(Ingredient.name).contains(normalized_query),
            )
            .order_by(
                Ingredient.name.asc(),
            )
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def get_low_stock(
        self,
        restaurant_id: UUID,
    ) -> list[Ingredient]:
        result = await self.db.execute(
            select(Ingredient)
            .where(
                Ingredient.restaurant_id == restaurant_id,
                Ingredient.current_stock <= Ingredient.minimum_stock,
            )
            .order_by(
                Ingredient.current_stock.asc(),
                Ingredient.name.asc(),
            )
        )

        return list(result.scalars().all())
