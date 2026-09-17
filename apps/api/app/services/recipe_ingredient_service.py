from uuid import UUID

from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)
from app.repositories.recipe_repository import RecipeRepository
from app.services.ingredient_service import IngredientService
from app.schemas.recipe_ingredient import (
    RecipeIngredientCreate,
    RecipeIngredientUpdate,
)


class RecipeIngredientService:
    def __init__(
        self,
        repository: RecipeIngredientRepository,
        recipe_repository: RecipeRepository,
        ingredient_service: IngredientService,
    ):
        self.repository = repository
        self.recipe_repository = recipe_repository
        self.ingredient_service = ingredient_service

    async def add_ingredient(
        self,
        restaurant_id: UUID,
        recipe_id: UUID,
        data: RecipeIngredientCreate,
    ):
        recipe = await self.recipe_repository.get_by_id(
            restaurant_id=restaurant_id,
            recipe_id=recipe_id,
        )

        if recipe is None:
            return None

        ingredient = await self.ingredient_service.get_ingredient(
            restaurant_id=restaurant_id,
            ingredient_id=data.ingredient_id,
        )

        if ingredient is None:
            return None

        existing = await self.repository.get_by_recipe_and_ingredient(
            recipe_id=recipe_id,
            ingredient_id=data.ingredient_id,
        )

        if existing is not None:
            return None

        recipe_ingredient = await self.repository.create(
            recipe_id=recipe_id,
            ingredient_id=data.ingredient_id,
            quantity=data.quantity,
        )

        await self.repository.db.commit()
        await self.repository.db.refresh(recipe_ingredient)

        return recipe_ingredient

    async def list_ingredients(
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

        return await self.repository.get_by_recipe(
            recipe_id=recipe_id,
        )

    async def update_ingredient(
        self,
        restaurant_id: UUID,
        recipe_id: UUID,
        recipe_ingredient_id: UUID,
        data: RecipeIngredientUpdate,
    ):
        recipe = await self.recipe_repository.get_by_id(
            restaurant_id=restaurant_id,
            recipe_id=recipe_id,
        )

        if recipe is None:
            return None

        recipe_ingredient = await self.repository.get_by_id(
            recipe_ingredient_id=recipe_ingredient_id,
        )

        if recipe_ingredient is None:
            return None

        if recipe_ingredient.recipe_id != recipe_id:
            return None

        recipe_ingredient = await self.repository.update(
            recipe_ingredient=recipe_ingredient,
            quantity=data.quantity,
        )

        await self.repository.db.commit()
        await self.repository.db.refresh(recipe_ingredient)

        return recipe_ingredient

    async def delete_ingredient(
        self,
        restaurant_id: UUID,
        recipe_id: UUID,
        recipe_ingredient_id: UUID,
    ):
        recipe = await self.recipe_repository.get_by_id(
            restaurant_id=restaurant_id,
            recipe_id=recipe_id,
        )

        if recipe is None:
            return False

        recipe_ingredient = await self.repository.get_by_id(
            recipe_ingredient_id=recipe_ingredient_id,
        )

        if recipe_ingredient is None:
            return False

        if recipe_ingredient.recipe_id != recipe_id:
            return False

        await self.repository.delete(recipe_ingredient)

        await self.repository.db.commit()

        return True