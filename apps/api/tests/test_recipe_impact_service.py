from decimal import Decimal
from uuid import uuid4

import pytest

from app.services.recipe_impact_service import RecipeImpactService


class FakeIngredient:
    def __init__(
        self,
        name,
        unit,
        current_stock,
        minimum_stock,
        restaurant_id,
    ):
        self.id = uuid4()
        self.name = name
        self.unit = unit
        self.current_stock = current_stock
        self.minimum_stock = minimum_stock
        self.restaurant_id = restaurant_id


class FakeRecipe:
    def __init__(
        self,
        name,
        restaurant_id,
    ):
        self.id = uuid4()
        self.name = name
        self.restaurant_id = restaurant_id


class FakeRecipeIngredient:
    def __init__(
        self,
        ingredient,
        quantity,
    ):
        self.id = uuid4()
        self.recipe_id = None
        self.ingredient_id = ingredient.id
        self.ingredient = ingredient
        self.quantity = quantity


class FakeIngredientService:
    def __init__(
        self,
        low_stock=None,
    ):
        self.low_stock = low_stock or []

    async def get_low_stock(
        self,
        restaurant_id,
    ):
        return [
            ingredient
            for ingredient in self.low_stock
            if ingredient.restaurant_id == restaurant_id
        ]


class FakeRecipeRepository:
    def __init__(
        self,
        recipes,
    ):
        self.recipes = recipes

    async def get_all(
        self,
        restaurant_id,
    ):
        return [
            recipe
            for recipe in self.recipes
            if recipe.restaurant_id == restaurant_id
        ]


class FakeRecipeIngredientRepository:
    def __init__(
        self,
        ingredients_by_recipe,
    ):
        self.ingredients_by_recipe = ingredients_by_recipe

    async def get_by_recipe(
        self,
        recipe_id,
    ):
        return self.ingredients_by_recipe.get(
            recipe_id,
            [],
        )


def make_service(
    recipes,
    recipe_ingredients,
    low_stock,
):
    return RecipeImpactService(
        recipe_repository=FakeRecipeRepository(
            recipes,
        ),
        recipe_ingredient_repository=FakeRecipeIngredientRepository(
            recipe_ingredients,
        ),
        ingredient_service=FakeIngredientService(
            low_stock=low_stock,
        ),
    )


@pytest.mark.asyncio
async def test_no_low_stock_ingredients_returns_empty_list():
    restaurant_id = uuid4()

    tomato = FakeIngredient(
        name="Tomato",
        unit="kg",
        current_stock=5,
        minimum_stock=2,
        restaurant_id=restaurant_id,
    )

    recipe = FakeRecipe(
        name="Margherita Pizza",
        restaurant_id=restaurant_id,
    )

    service = make_service(
        recipes=[recipe],
        recipe_ingredients={
            recipe.id: [
                FakeRecipeIngredient(
                    tomato,
                    Decimal("0.2"),
                ),
            ],
        },
        low_stock=[],
    )

    result = await service.get_low_stock_recipe_impact(
        restaurant_id=restaurant_id,
    )

    assert result == []


@pytest.mark.asyncio
async def test_one_low_stock_ingredient_affects_one_recipe():
    restaurant_id = uuid4()

    tomato = FakeIngredient(
        name="Tomato",
        unit="kg",
        current_stock=Decimal("0.5"),
        minimum_stock=Decimal("2"),
        restaurant_id=restaurant_id,
    )

    recipe = FakeRecipe(
        name="Margherita Pizza",
        restaurant_id=restaurant_id,
    )

    service = make_service(
        recipes=[recipe],
        recipe_ingredients={
            recipe.id: [
                FakeRecipeIngredient(
                    tomato,
                    Decimal("0.2"),
                ),
            ],
        },
        low_stock=[tomato],
    )

    result = await service.get_low_stock_recipe_impact(
        restaurant_id=restaurant_id,
    )

    assert len(result) == 1
    assert result[0]["recipe_id"] == recipe.id
    assert result[0]["recipe_name"] == "Margherita Pizza"

    assert len(result[0]["affected_ingredients"]) == 1

    affected = result[0]["affected_ingredients"][0]

    assert affected["ingredient_id"] == tomato.id
    assert affected["ingredient_name"] == "Tomato"
    assert affected["current_stock"] == Decimal("0.5")
    assert affected["minimum_stock"] == Decimal("2")
    assert affected["unit"] == "kg"
    assert affected["required_quantity"] == Decimal("0.2")


@pytest.mark.asyncio
async def test_one_low_stock_ingredient_affects_multiple_recipes():
    restaurant_id = uuid4()

    tomato = FakeIngredient(
        name="Tomato",
        unit="kg",
        current_stock=Decimal("0.5"),
        minimum_stock=Decimal("2"),
        restaurant_id=restaurant_id,
    )

    pizza = FakeRecipe(
        name="Margherita Pizza",
        restaurant_id=restaurant_id,
    )

    pasta = FakeRecipe(
        name="Tomato Pasta",
        restaurant_id=restaurant_id,
    )

    service = make_service(
        recipes=[
            pizza,
            pasta,
        ],
        recipe_ingredients={
            pizza.id: [
                FakeRecipeIngredient(
                    tomato,
                    Decimal("0.2"),
                ),
            ],
            pasta.id: [
                FakeRecipeIngredient(
                    tomato,
                    Decimal("0.3"),
                ),
            ],
        },
        low_stock=[tomato],
    )

    result = await service.get_low_stock_recipe_impact(
        restaurant_id=restaurant_id,
    )

    assert len(result) == 2

    recipe_names = {
        recipe["recipe_name"]
        for recipe in result
    }

    assert recipe_names == {
        "Margherita Pizza",
        "Tomato Pasta",
    }


@pytest.mark.asyncio
async def test_recipe_without_low_stock_ingredients_is_excluded():
    restaurant_id = uuid4()

    tomato = FakeIngredient(
        name="Tomato",
        unit="kg",
        current_stock=Decimal("0.5"),
        minimum_stock=Decimal("2"),
        restaurant_id=restaurant_id,
    )

    cheese = FakeIngredient(
        name="Cheese",
        unit="kg",
        current_stock=Decimal("5"),
        minimum_stock=Decimal("2"),
        restaurant_id=restaurant_id,
    )

    affected_recipe = FakeRecipe(
        name="Tomato Pasta",
        restaurant_id=restaurant_id,
    )

    unaffected_recipe = FakeRecipe(
        name="Cheese Pasta",
        restaurant_id=restaurant_id,
    )

    service = make_service(
        recipes=[
            affected_recipe,
            unaffected_recipe,
        ],
        recipe_ingredients={
            affected_recipe.id: [
                FakeRecipeIngredient(
                    tomato,
                    Decimal("0.3"),
                ),
            ],
            unaffected_recipe.id: [
                FakeRecipeIngredient(
                    cheese,
                    Decimal("0.2"),
                ),
            ],
        },
        low_stock=[tomato],
    )

    result = await service.get_low_stock_recipe_impact(
        restaurant_id=restaurant_id,
    )

    assert len(result) == 1
    assert result[0]["recipe_name"] == "Tomato Pasta"


@pytest.mark.asyncio
async def test_recipe_impact_is_scoped_to_restaurant():
    restaurant_id = uuid4()
    other_restaurant_id = uuid4()

    tomato = FakeIngredient(
        name="Tomato",
        unit="kg",
        current_stock=Decimal("0.5"),
        minimum_stock=Decimal("2"),
        restaurant_id=other_restaurant_id,
    )

    recipe = FakeRecipe(
        name="Other Restaurant Pasta",
        restaurant_id=other_restaurant_id,
    )

    service = make_service(
        recipes=[recipe],
        recipe_ingredients={
            recipe.id: [
                FakeRecipeIngredient(
                    tomato,
                    Decimal("0.3"),
                ),
            ],
        },
        low_stock=[tomato],
    )

    result = await service.get_low_stock_recipe_impact(
        restaurant_id=restaurant_id,
    )

    assert result == []