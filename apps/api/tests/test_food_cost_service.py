from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant import Restaurant
from app.repositories.ingredient_repository import IngredientRepository
from app.repositories.recipe_ingredient_repository import (
    RecipeIngredientRepository,
)
from app.repositories.recipe_repository import RecipeRepository
from app.schemas.ingredient import IngredientCreate
from app.schemas.recipe import RecipeCreate
from app.schemas.recipe_ingredient import RecipeIngredientCreate
from app.services.food_cost_service import FoodCostService
from app.services.ingredient_service import IngredientService
from app.services.recipe_ingredient_service import RecipeIngredientService
from app.services.recipe_service import RecipeService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def create_restaurant(
    db_session: AsyncSession,
    restaurant_id,
):
    restaurant = Restaurant(
        id=restaurant_id,
        name="Test Restaurant",
        slug=f"test-restaurant-{restaurant_id}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    return restaurant


async def create_ingredient(
    db_session: AsyncSession,
    restaurant_id,
    name: str,
    unit: str,
    cost_per_unit: Decimal,
):
    ingredient_repository = IngredientRepository(db_session)
    ingredient_service = IngredientService(ingredient_repository)

    return await ingredient_service.create_ingredient(
        IngredientCreate(
            restaurant_id=restaurant_id,
            name=name,
            unit=unit,
            cost_per_unit=cost_per_unit,
        )
    )


async def create_recipe(
    db_session: AsyncSession,
    restaurant_id,
    name: str = "Test Recipe",
):
    recipe_repository = RecipeRepository(db_session)
    recipe_service = RecipeService(recipe_repository)

    return await recipe_service.create_recipe(
        RecipeCreate(
            restaurant_id=restaurant_id,
            name=name,
        )
    )


async def add_recipe_ingredient(
    db_session: AsyncSession,
    restaurant_id,
    recipe_id,
    ingredient_id,
    quantity: Decimal,
):
    recipe_ingredient_repository = RecipeIngredientRepository(
        db_session
    )

    recipe_repository = RecipeRepository(db_session)

    ingredient_repository = IngredientRepository(db_session)
    ingredient_service = IngredientService(ingredient_repository)

    recipe_ingredient_service = RecipeIngredientService(
        repository=recipe_ingredient_repository,
        recipe_repository=recipe_repository,
        ingredient_service=ingredient_service,
    )

    return await recipe_ingredient_service.add_ingredient(
        restaurant_id=restaurant_id,
        recipe_id=recipe_id,
        data=RecipeIngredientCreate(
            recipe_id=recipe_id,
            ingredient_id=ingredient_id,
            quantity=quantity,
        ),
    )


def create_food_cost_service(
    db_session: AsyncSession,
):
    recipe_repository = RecipeRepository(db_session)

    recipe_ingredient_repository = RecipeIngredientRepository(
        db_session
    )

    ingredient_repository = IngredientRepository(db_session)

    return FoodCostService(
        recipe_repository=recipe_repository,
        recipe_ingredient_repository=recipe_ingredient_repository,
        ingredient_repository=ingredient_repository,
    )


# ---------------------------------------------------------------------------
# Food Cost Tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_calculate_food_cost(
    db_session: AsyncSession,
):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session,
        restaurant_id,
    )

    recipe = await create_recipe(
        db_session,
        restaurant_id=restaurant_id,
        name="Pasta Carbonara",
    )

    pasta = await create_ingredient(
        db_session,
        restaurant_id=restaurant_id,
        name="Pasta",
        unit="kg",
        cost_per_unit=Decimal("3.33"),
    )

    await add_recipe_ingredient(
        db_session=db_session,
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
        ingredient_id=pasta.id,
        quantity=Decimal("0.333"),
    )

    service = create_food_cost_service(db_session)

    result = await service.calculate_food_cost(
        recipe_id=recipe.id,
        restaurant_id=restaurant_id,
    )

    expected_cost = (
        Decimal("3.33") * Decimal("0.333")
    ).quantize(Decimal("0.01"))

    assert result["recipe_id"] == recipe.id
    assert result["recipe_name"] == "Pasta Carbonara"

    assert Decimal(str(result["food_cost"])) == expected_cost

    assert len(result["breakdown"]) == 1

    breakdown = result["breakdown"][0]

    assert breakdown["ingredient"] == "Pasta"
    assert Decimal(str(breakdown["quantity"])) == Decimal("0.333")
    assert Decimal(str(breakdown["cost_per_unit"])) == Decimal("3.33")
    assert Decimal(str(breakdown["total_cost"])) == expected_cost


@pytest.mark.anyio
async def test_calculate_food_cost_with_multiple_ingredients(
    db_session: AsyncSession,
):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session,
        restaurant_id,
    )

    recipe = await create_recipe(
        db_session,
        restaurant_id=restaurant_id,
        name="Tomato Pasta",
    )

    pasta = await create_ingredient(
        db_session,
        restaurant_id=restaurant_id,
        name="Pasta",
        unit="kg",
        cost_per_unit=Decimal("4.00"),
    )

    tomato = await create_ingredient(
        db_session,
        restaurant_id=restaurant_id,
        name="Tomato",
        unit="kg",
        cost_per_unit=Decimal("2.50"),
    )

    await add_recipe_ingredient(
        db_session=db_session,
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
        ingredient_id=pasta.id,
        quantity=Decimal("0.5"),
    )

    await add_recipe_ingredient(
        db_session=db_session,
        restaurant_id=restaurant_id,
        recipe_id=recipe.id,
        ingredient_id=tomato.id,
        quantity=Decimal("0.2"),
    )

    service = create_food_cost_service(db_session)

    result = await service.calculate_food_cost(
        recipe_id=recipe.id,
        restaurant_id=restaurant_id,
    )

    expected_pasta_cost = (
        Decimal("4.00") * Decimal("0.5")
    )

    expected_tomato_cost = (
        Decimal("2.50") * Decimal("0.2")
    )

    expected_total = (
        expected_pasta_cost + expected_tomato_cost
    ).quantize(Decimal("0.01"))

    assert result["recipe_id"] == recipe.id
    assert result["recipe_name"] == "Tomato Pasta"

    assert Decimal(str(result["food_cost"])) == expected_total

    assert len(result["breakdown"]) == 2

    pasta_breakdown = next(
        item
        for item in result["breakdown"]
        if item["ingredient"] == "Pasta"
    )

    tomato_breakdown = next(
        item
        for item in result["breakdown"]
        if item["ingredient"] == "Tomato"
    )

    assert Decimal(
        str(pasta_breakdown["quantity"])
    ) == Decimal("0.5")

    assert Decimal(
        str(pasta_breakdown["cost_per_unit"])
    ) == Decimal("4.00")

    assert Decimal(
        str(pasta_breakdown["total_cost"])
    ) == Decimal("2.00")

    assert Decimal(
        str(tomato_breakdown["quantity"])
    ) == Decimal("0.2")

    assert Decimal(
        str(tomato_breakdown["cost_per_unit"])
    ) == Decimal("2.50")

    assert Decimal(
        str(tomato_breakdown["total_cost"])
    ) == Decimal("0.50")


@pytest.mark.anyio
async def test_calculate_food_cost_for_recipe_with_no_ingredients(
    db_session: AsyncSession,
):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session,
        restaurant_id,
    )

    recipe = await create_recipe(
        db_session,
        restaurant_id=restaurant_id,
        name="Empty Recipe",
    )

    service = create_food_cost_service(db_session)

    result = await service.calculate_food_cost(
        recipe_id=recipe.id,
        restaurant_id=restaurant_id,
    )

    assert result["recipe_id"] == recipe.id
    assert result["recipe_name"] == "Empty Recipe"
    assert Decimal(str(result["food_cost"])) == Decimal("0.00")
    assert result["breakdown"] == []


@pytest.mark.anyio
async def test_calculate_food_cost_recipe_not_found(
    db_session: AsyncSession,
):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session,
        restaurant_id,
    )

    service = create_food_cost_service(db_session)

    result = await service.calculate_food_cost(
        recipe_id=uuid4(),
        restaurant_id=restaurant_id,
    )

    assert result is None


@pytest.mark.anyio
async def test_calculate_food_cost_wrong_restaurant(
    db_session: AsyncSession,
):
    restaurant_id = uuid4()
    another_restaurant_id = uuid4()

    await create_restaurant(
        db_session,
        restaurant_id,
    )

    await create_restaurant(
        db_session,
        another_restaurant_id,
    )

    recipe = await create_recipe(
        db_session,
        restaurant_id=restaurant_id,
        name="Private Recipe",
    )

    service = create_food_cost_service(db_session)

    result = await service.calculate_food_cost(
        recipe_id=recipe.id,
        restaurant_id=another_restaurant_id,
    )

    assert result is None


# ---------------------------------------------------------------------------
# Validation Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "quantity",
    [
        Decimal("0"),
        Decimal("-1"),
    ],
)
def test_non_positive_quantity_is_rejected(
    quantity,
):
    with pytest.raises(ValidationError):
        RecipeIngredientCreate(
            ingredient_id=uuid4(),
            recipe_id=uuid4(),
            quantity=quantity,
        )

