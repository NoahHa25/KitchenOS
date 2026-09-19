from uuid import uuid4

import pytest

from app.schemas.recipe_ingredient import (
    RecipeIngredientCreate,
    RecipeIngredientUpdate,
)
from app.services.recipe_ingredient_service import (
    RecipeIngredientService,
)


class FakeDatabase:
    def __init__(self):
        self.commit_called = False
        self.refresh_called = False

    async def commit(self):
        self.commit_called = True

    async def refresh(self, obj):
        self.refresh_called = True
        return obj


class FakeRecipe:
    def __init__(self, restaurant_id):
        self.id = uuid4()
        self.restaurant_id = restaurant_id


class FakeIngredient:
    def __init__(
        self,
        restaurant_id,
        name="Tomato",
    ):
        self.id = uuid4()
        self.restaurant_id = restaurant_id
        self.name = name


class FakeRecipeIngredient:
    def __init__(
        self,
        recipe_id,
        ingredient_id,
        quantity=1.0,
    ):
        self.id = uuid4()
        self.recipe_id = recipe_id
        self.ingredient_id = ingredient_id
        self.quantity = quantity


class FakeRecipeRepository:
    def __init__(self, recipes=None):
        self.recipes = recipes or []

    async def get_by_id(
        self,
        restaurant_id,
        recipe_id,
    ):
        for recipe in self.recipes:
            if (
                recipe.id == recipe_id
                and recipe.restaurant_id == restaurant_id
            ):
                return recipe

        return None


class FakeIngredientService:
    def __init__(self, ingredients=None):
        self.ingredients = ingredients or []

    async def get_ingredient(
        self,
        restaurant_id,
        ingredient_id,
    ):
        for ingredient in self.ingredients:
            if (
                ingredient.id == ingredient_id
                and ingredient.restaurant_id == restaurant_id
            ):
                return ingredient

        return None


class FakeRecipeIngredientRepository:
    def __init__(self, recipe_ingredients=None):
        self.db = FakeDatabase()
        self.recipe_ingredients = recipe_ingredients or []

        self.created_args = None
        self.updated_args = None
        self.deleted_recipe_ingredient = None

    async def create(
        self,
        recipe_id,
        ingredient_id,
        quantity,
    ):
        self.created_args = {
            "recipe_id": recipe_id,
            "ingredient_id": ingredient_id,
            "quantity": quantity,
        }

        recipe_ingredient = FakeRecipeIngredient(
            recipe_id=recipe_id,
            ingredient_id=ingredient_id,
            quantity=quantity,
        )

        self.recipe_ingredients.append(recipe_ingredient)

        return recipe_ingredient

    async def get_by_id(
        self,
        recipe_ingredient_id,
    ):
        for recipe_ingredient in self.recipe_ingredients:
            if recipe_ingredient.id == recipe_ingredient_id:
                return recipe_ingredient

        return None

    async def get_by_recipe(
        self,
        recipe_id,
    ):
        return [
            recipe_ingredient
            for recipe_ingredient in self.recipe_ingredients
            if recipe_ingredient.recipe_id == recipe_id
        ]

    async def get_by_recipe_and_ingredient(
        self,
        recipe_id,
        ingredient_id,
    ):
        for recipe_ingredient in self.recipe_ingredients:
            if (
                recipe_ingredient.recipe_id == recipe_id
                and recipe_ingredient.ingredient_id == ingredient_id
            ):
                return recipe_ingredient

        return None

    async def update(
        self,
        recipe_ingredient,
        quantity,
    ):
        self.updated_args = {
            "recipe_ingredient": recipe_ingredient,
            "quantity": quantity,
        }

        recipe_ingredient.quantity = quantity

        return recipe_ingredient

    async def delete(
        self,
        recipe_ingredient,
    ):
        self.deleted_recipe_ingredient = recipe_ingredient

        if recipe_ingredient in self.recipe_ingredients:
            self.recipe_ingredients.remove(recipe_ingredient)


def make_service(
    restaurant_id,
    recipe=None,
    ingredient=None,
    recipe_ingredients=None,
):
    recipe_repository = FakeRecipeRepository(
        recipes=[recipe] if recipe else [],
    )

    ingredient_service = FakeIngredientService(
        ingredients=[ingredient] if ingredient else [],
    )

    repository = FakeRecipeIngredientRepository(
        recipe_ingredients=recipe_ingredients,
    )

    service = RecipeIngredientService(
        repository=repository,
        recipe_repository=recipe_repository,
        ingredient_service=ingredient_service,
    )

    return service, repository


@pytest.mark.anyio
async def test_add_ingredient_to_recipe():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
    )

    ingredient = FakeIngredient(
        restaurant_id=restaurant_id,
    )

    service, repository = make_service(
        restaurant_id=restaurant_id,
        recipe=recipe,
        ingredient=ingredient,
    )

    data = RecipeIngredientCreate(
        ingredient_id=ingredient.id,
        quantity=2.5,
    )

    result = await service.add_ingredient(
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
        data=data,
    )

    assert result is not None
    assert result.recipe_id == recipe.id
    assert result.ingredient_id == ingredient.id
    assert result.quantity == 2.5

    assert repository.created_args == {
        "recipe_id": recipe.id,
        "ingredient_id": ingredient.id,
        "quantity": 2.5,
    }

    assert repository.db.commit_called is True
    assert repository.db.refresh_called is True


@pytest.mark.anyio
async def test_add_ingredient_returns_none_when_recipe_does_not_exist():
    restaurant_id = uuid4()
    ingredient = FakeIngredient(
        restaurant_id=restaurant_id,
    )

    service, repository = make_service(
        restaurant_id=restaurant_id,
        ingredient=ingredient,
    )

    data = RecipeIngredientCreate(
        ingredient_id=ingredient.id,
        quantity=1,
    )

    result = await service.add_ingredient(
        restaurant_id=restaurant_id,
        recipe_id=uuid4(),
        data=data,
    )

    assert result is None
    assert repository.created_args is None
    assert repository.db.commit_called is False


@pytest.mark.anyio
async def test_add_ingredient_returns_none_when_ingredient_does_not_exist():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
    )

    service, repository = make_service(
        restaurant_id=restaurant_id,
        recipe=recipe,
    )

    data = RecipeIngredientCreate(
        ingredient_id=uuid4(),
        quantity=1,
    )

    result = await service.add_ingredient(
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
        data=data,
    )

    assert result is None
    assert repository.created_args is None
    assert repository.db.commit_called is False


@pytest.mark.anyio
async def test_add_duplicate_ingredient_returns_none():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
    )

    ingredient = FakeIngredient(
        restaurant_id=restaurant_id,
    )

    existing = FakeRecipeIngredient(
        recipe_id=recipe.id,
        ingredient_id=ingredient.id,
        quantity=1,
    )

    service, repository = make_service(
        restaurant_id=restaurant_id,
        recipe=recipe,
        ingredient=ingredient,
        recipe_ingredients=[existing],
    )

    data = RecipeIngredientCreate(
        ingredient_id=ingredient.id,
        quantity=2,
    )

    result = await service.add_ingredient(
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
        data=data,
    )

    assert result is None
    assert repository.created_args is None
    assert repository.db.commit_called is False


@pytest.mark.anyio
async def test_list_ingredients_returns_recipe_ingredients():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
    )

    ingredient = FakeIngredient(
        restaurant_id=restaurant_id,
    )

    recipe_ingredient = FakeRecipeIngredient(
        recipe_id=recipe.id,
        ingredient_id=ingredient.id,
        quantity=3,
    )

    service, _ = make_service(
        restaurant_id=restaurant_id,
        recipe=recipe,
        ingredient=ingredient,
        recipe_ingredients=[recipe_ingredient],
    )

    result = await service.list_ingredients(
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
    )

    assert result == [recipe_ingredient]


@pytest.mark.anyio
async def test_list_ingredients_returns_none_for_missing_recipe():
    restaurant_id = uuid4()

    service, _ = make_service(
        restaurant_id=restaurant_id,
    )

    result = await service.list_ingredients(
        restaurant_id=restaurant_id,
        recipe_id=uuid4(),
    )

    assert result is None


@pytest.mark.anyio
async def test_update_ingredient_quantity():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
    )

    ingredient = FakeIngredient(
        restaurant_id=restaurant_id,
    )

    recipe_ingredient = FakeRecipeIngredient(
        recipe_id=recipe.id,
        ingredient_id=ingredient.id,
        quantity=1,
    )

    service, repository = make_service(
        restaurant_id=restaurant_id,
        recipe=recipe,
        ingredient=ingredient,
        recipe_ingredients=[recipe_ingredient],
    )

    data = RecipeIngredientUpdate(
        quantity=4.5,
    )

    result = await service.update_ingredient(
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
        recipe_ingredient_id=recipe_ingredient.id,
        data=data,
    )

    assert result is recipe_ingredient
    assert recipe_ingredient.quantity == 4.5

    assert repository.db.commit_called is True
    assert repository.db.refresh_called is True


@pytest.mark.anyio
async def test_update_ingredient_rejects_wrong_recipe():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
    )

    another_recipe = FakeRecipe(
        restaurant_id=restaurant_id,
    )

    ingredient = FakeIngredient(
        restaurant_id=restaurant_id,
    )

    recipe_ingredient = FakeRecipeIngredient(
        recipe_id=another_recipe.id,
        ingredient_id=ingredient.id,
        quantity=1,
    )

    service, repository = make_service(
        restaurant_id=restaurant_id,
        recipe=recipe,
        ingredient=ingredient,
        recipe_ingredients=[recipe_ingredient],
    )

    data = RecipeIngredientUpdate(
        quantity=5,
    )

    result = await service.update_ingredient(
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
        recipe_ingredient_id=recipe_ingredient.id,
        data=data,
    )

    assert result is None
    assert recipe_ingredient.quantity == 1
    assert repository.updated_args is None
    assert repository.db.commit_called is False


@pytest.mark.anyio
async def test_update_ingredient_returns_none_when_not_found():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
    )

    service, repository = make_service(
        restaurant_id=restaurant_id,
        recipe=recipe,
    )

    data = RecipeIngredientUpdate(
        quantity=5,
    )

    result = await service.update_ingredient(
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
        recipe_ingredient_id=uuid4(),
        data=data,
    )

    assert result is None
    assert repository.updated_args is None
    assert repository.db.commit_called is False


@pytest.mark.anyio
async def test_delete_ingredient():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
    )

    ingredient = FakeIngredient(
        restaurant_id=restaurant_id,
    )

    recipe_ingredient = FakeRecipeIngredient(
        recipe_id=recipe.id,
        ingredient_id=ingredient.id,
        quantity=1,
    )

    service, repository = make_service(
        restaurant_id=restaurant_id,
        recipe=recipe,
        ingredient=ingredient,
        recipe_ingredients=[recipe_ingredient],
    )

    result = await service.delete_ingredient(
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
        recipe_ingredient_id=recipe_ingredient.id,
    )

    assert result is True
    assert repository.deleted_recipe_ingredient is recipe_ingredient
    assert recipe_ingredient not in repository.recipe_ingredients
    assert repository.db.commit_called is True


@pytest.mark.anyio
async def test_delete_ingredient_rejects_wrong_recipe():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
    )

    another_recipe = FakeRecipe(
        restaurant_id=restaurant_id,
    )

    ingredient = FakeIngredient(
        restaurant_id=restaurant_id,
    )

    recipe_ingredient = FakeRecipeIngredient(
        recipe_id=another_recipe.id,
        ingredient_id=ingredient.id,
        quantity=1,
    )

    service, repository = make_service(
        restaurant_id=restaurant_id,
        recipe=recipe,
        ingredient=ingredient,
        recipe_ingredients=[recipe_ingredient],
    )

    result = await service.delete_ingredient(
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
        recipe_ingredient_id=recipe_ingredient.id,
    )

    assert result is False
    assert repository.deleted_recipe_ingredient is None
    assert repository.db.commit_called is False


@pytest.mark.anyio
async def test_delete_ingredient_returns_false_when_not_found():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
    )

    service, repository = make_service(
        restaurant_id=restaurant_id,
        recipe=recipe,
    )

    result = await service.delete_ingredient(
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
        recipe_ingredient_id=uuid4(),
    )

    assert result is False
    assert repository.deleted_recipe_ingredient is None
    assert repository.db.commit_called is False

