from decimal import Decimal
from uuid import uuid4

import pytest

from app.schemas.recipe import RecipeCreate, RecipeUpdate
from app.services.recipe_service import RecipeService


class FakeDatabase:
    def __init__(self):
        self.commit_called = False
        self.rollback_called = False

    async def commit(self):
        self.commit_called = True

    async def rollback(self):
        self.rollback_called = True

    async def refresh(self, obj):
        return obj


class FakeRecipe:
    def __init__(
        self,
        restaurant_id,
        name="Pasta",
        description="Classic pasta",
        selling_price=Decimal("0.00"),
        portion_size=1.0,
        portion_unit="portion",
        is_active=True,
    ):
        self.id = uuid4()
        self.restaurant_id = restaurant_id
        self.name = name
        self.description = description
        self.selling_price = selling_price
        self.portion_size = portion_size
        self.portion_unit = portion_unit
        self.is_active = is_active


class FakeRecipeRepository:
    def __init__(self, recipe=None):
        self.db = FakeDatabase()
        self.recipe = recipe
        self.recipes = []

        if recipe is not None:
            self.recipes.append(recipe)

        self.created_args = None
        self.updated_args = None
        self.deleted_recipe = None

    async def create(
        self,
        restaurant_id,
        name,
        description=None,
        selling_price=Decimal("0.00"),
        portion_size=1.0,
        portion_unit="portion",
        is_active=True,
    ):
        self.created_args = {
            "restaurant_id": restaurant_id,
            "name": name,
            "description": description,
            "selling_price": selling_price,
            "portion_size": portion_size,
            "portion_unit": portion_unit,
            "is_active": is_active,
        }

        recipe = FakeRecipe(
            restaurant_id=restaurant_id,
            name=name,
            description=description,
            selling_price=selling_price,
            portion_size=portion_size,
            portion_unit=portion_unit,
            is_active=is_active,
        )

        self.recipes.append(recipe)
        self.recipe = recipe

        return recipe

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

    async def get_all(self, restaurant_id):
        return [
            recipe
            for recipe in self.recipes
            if recipe.restaurant_id == restaurant_id
        ]

    async def update(
        self,
        recipe,
        name=None,
        description=None,
        selling_price=None,
        portion_size=None,
        portion_unit=None,
        is_active=None,
    ):
        self.updated_args = {
            "recipe": recipe,
            "name": name,
            "description": description,
            "selling_price": selling_price,
            "portion_size": portion_size,
            "portion_unit": portion_unit,
            "is_active": is_active,
        }

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

        return recipe

    async def delete(self, recipe):
        self.deleted_recipe = recipe

        if recipe in self.recipes:
            self.recipes.remove(recipe)


def make_service(recipe=None):
    repository = FakeRecipeRepository(recipe=recipe)
    service = RecipeService(repository)

    return service, repository


@pytest.mark.anyio
async def test_create_recipe():
    restaurant_id = uuid4()

    service, repository = make_service()

    data = RecipeCreate(
        restaurant_id=restaurant_id,
        name="Carbonara",
        description="Creamy pasta",
    )

    recipe = await service.create_recipe(data)

    assert recipe.restaurant_id == restaurant_id
    assert recipe.name == "Carbonara"
    assert recipe.description == "Creamy pasta"
    assert recipe.selling_price == Decimal("0.00")
    assert recipe.portion_size == 1.0
    assert recipe.portion_unit == "portion"
    assert recipe.is_active is True

    assert repository.created_args == {
        "restaurant_id": restaurant_id,
        "name": "Carbonara",
        "description": "Creamy pasta",
        "selling_price": Decimal("0.00"),
        "portion_size": 1.0,
        "portion_unit": "portion",
        "is_active": True,
    }

    assert repository.db.commit_called is True


@pytest.mark.anyio
async def test_list_recipes_is_scoped_to_restaurant():
    restaurant_a = uuid4()
    restaurant_b = uuid4()

    recipe_a = FakeRecipe(
        restaurant_id=restaurant_a,
        name="Pizza",
    )

    recipe_b = FakeRecipe(
        restaurant_id=restaurant_b,
        name="Burger",
    )

    repository = FakeRecipeRepository(recipe=recipe_a)
    repository.recipes.append(recipe_b)

    service = RecipeService(repository)

    recipes = await service.list_recipes(
        restaurant_id=restaurant_a,
    )

    assert recipes == [recipe_a]


@pytest.mark.anyio
async def test_get_recipe_returns_recipe_for_correct_restaurant():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
        name="Risotto",
    )

    service, repository = make_service(recipe)

    result = await service.get_recipe(
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
    )

    assert result is recipe


@pytest.mark.anyio
async def test_get_recipe_returns_none_for_wrong_restaurant():
    restaurant_id = uuid4()
    another_restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
        name="Risotto",
    )

    service, _ = make_service(recipe)

    result = await service.get_recipe(
        restaurant_id=another_restaurant_id,
        recipe_id=recipe.id,
    )

    assert result is None


@pytest.mark.anyio
async def test_update_recipe():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
        name="Old Name",
        description="Old description",
    )

    service, repository = make_service(recipe)

    data = RecipeUpdate(
        name="New Name",
        description="New description",
    )

    result = await service.update_recipe(
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
        data=data,
    )

    assert result is recipe
    assert recipe.name == "New Name"
    assert recipe.description == "New description"

    assert repository.updated_args == {
        "recipe": recipe,
        "name": "New Name",
        "description": "New description",
        "selling_price": None,
        "portion_size": None,
        "portion_unit": None,
        "is_active": None,
    }

    assert repository.db.commit_called is True


@pytest.mark.anyio
async def test_update_recipe_returns_none_when_recipe_does_not_exist():
    service, repository = make_service()

    data = RecipeUpdate(
        name="Updated",
    )

    result = await service.update_recipe(
        restaurant_id=uuid4(),
        recipe_id=uuid4(),
        data=data,
    )

    assert result is None
    assert repository.db.commit_called is False


@pytest.mark.anyio
async def test_delete_recipe():
    restaurant_id = uuid4()

    recipe = FakeRecipe(
        restaurant_id=restaurant_id,
        name="Delete Me",
    )

    service, repository = make_service(recipe)

    result = await service.delete_recipe(
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
    )

    assert result is True
    assert repository.deleted_recipe is recipe
    assert recipe not in repository.recipes
    assert repository.db.commit_called is True


@pytest.mark.anyio
async def test_delete_recipe_returns_false_when_recipe_does_not_exist():
    service, repository = make_service()

    result = await service.delete_recipe(
        restaurant_id=uuid4(),
        recipe_id=uuid4(),
    )

    assert result is False
    assert repository.deleted_recipe is None
    assert repository.db.commit_called is False