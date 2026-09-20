from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recipe import Recipe


class RecipeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        restaurant_id: UUID,
        name: str,
        description: str | None = None,
        selling_price: Decimal = Decimal("0.00"),
        portion_size: float = 1.0,
        portion_unit: str = "portion",
        is_active: bool = True,
    ) -> Recipe:
        recipe = Recipe(
            restaurant_id=restaurant_id,
            name=name,
            description=description,
            selling_price=selling_price,
            portion_size=portion_size,
            portion_unit=portion_unit,
            is_active=is_active,
        )

        self.db.add(recipe)
        await self.db.flush()

        return recipe

    async def get_by_id(
        self,
        restaurant_id: UUID,
        recipe_id: UUID,
    ) -> Recipe | None:
        result = await self.db.execute(
            select(Recipe).where(
                Recipe.id == recipe_id,
                Recipe.restaurant_id == restaurant_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_all(
        self,
        restaurant_id: UUID,
    ) -> list[Recipe]:
        result = await self.db.execute(
            select(Recipe)
            .where(
                Recipe.restaurant_id == restaurant_id,
            )
            .order_by(Recipe.name.asc())
        )

        return list(result.scalars().all())

    async def update(
        self,
        recipe: Recipe,
        name: str | None = None,
        description: str | None = None,
        selling_price: Decimal | None = None,
        portion_size: float | None = None,
        portion_unit: str | None = None,
        is_active: bool | None = None,
    ) -> Recipe:
        if name is not None:
            recipe.name = name

        if description is not None:
            recipe.description = description

        if selling_price is not None:
            recipe.selling_price = selling_price

        if portion_size is not None:
            recipe.portion_size = portion_size

        if portion_unit is not None:
            recipe.portion_unit = portion_unit

        if is_active is not None:
            recipe.is_active = is_active

        await self.db.flush()

        return recipe

    async def delete(
        self,
        recipe: Recipe,
    ) -> None:
        await self.db.delete(recipe)
        await self.db.flush()