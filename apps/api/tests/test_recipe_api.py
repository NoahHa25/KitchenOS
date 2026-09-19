from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe
from app.models.recipe_ingredient import RecipeIngredient
from app.models.restaurant import Restaurant


# ---------------------------------------------------------------------------
# Database fixture
# ---------------------------------------------------------------------------


@pytest.fixture
async def db_session_factory():
    """
    Dedicated database engine for each API integration test.

    NullPool is intentional here.

    It prevents asyncpg connections from being reused across pytest
    event-loop boundaries and avoids the "another operation is in progress"
    error during integration tests.
    """
    test_engine = create_async_engine(
        settings.database_url,
        echo=True,
        poolclass=NullPool,
    )

    test_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        yield test_session_factory
    finally:
        await test_engine.dispose()


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


@pytest.fixture
async def client(db_session_factory):
    async def override_get_db():
        async with db_session_factory() as db:
            yield db

    previous_override = app.dependency_overrides.get(get_db)

    app.dependency_overrides[get_db] = override_get_db

    transport = httpx.ASGITransport(app=app)

    try:
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as test_client:
            yield test_client

    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


async def create_restaurant(
    session_factory,
    restaurant_id,
):
    async with session_factory() as db:
        restaurant = Restaurant(
            id=restaurant_id,
            name="Recipe API Test Restaurant",
            slug=f"recipe-api-test-{uuid4().hex}",
        )

        db.add(restaurant)
        await db.commit()


async def create_ingredient(
    session_factory,
    restaurant_id,
    *,
    name="Tomato",
    unit="kg",
    current_stock=Decimal("10.000"),
    minimum_stock=Decimal("1.000"),
    cost_per_unit=Decimal("4.50"),
):
    ingredient_id = uuid4()

    async with session_factory() as db:
        ingredient = Ingredient(
            id=ingredient_id,
            restaurant_id=restaurant_id,
            name=name,
            unit=unit,
            current_stock=current_stock,
            minimum_stock=minimum_stock,
            cost_per_unit=cost_per_unit,
        )

        db.add(ingredient)
        await db.commit()

    return ingredient_id


async def create_recipe(
    session_factory,
    restaurant_id,
    *,
    name="Tomato Pasta",
    description="Recipe API integration test",
):
    recipe_id = uuid4()

    async with session_factory() as db:
        recipe = Recipe(
            id=recipe_id,
            restaurant_id=restaurant_id,
            name=name,
            description=description,
        )

        db.add(recipe)
        await db.commit()

    return recipe_id


async def create_recipe_ingredient(
    session_factory,
    recipe_id,
    ingredient_id,
    *,
    quantity=Decimal("0.500"),
):
    recipe_ingredient_id = uuid4()

    async with session_factory() as db:
        recipe_ingredient = RecipeIngredient(
            id=recipe_ingredient_id,
            recipe_id=recipe_id,
            ingredient_id=ingredient_id,
            quantity=quantity,
        )

        db.add(recipe_ingredient)
        await db.commit()

    return recipe_ingredient_id


async def cleanup_restaurant(
    session_factory,
    restaurant_id,
):
    async with session_factory() as db:
        await db.execute(
            delete(RecipeIngredient).where(
                RecipeIngredient.recipe_id.in_(
                    select(Recipe.id).where(
                        Recipe.restaurant_id == restaurant_id,
                    )
                )
            )
        )

        await db.execute(
            delete(Recipe).where(
                Recipe.restaurant_id == restaurant_id,
            )
        )

        await db.execute(
            delete(Ingredient).where(
                Ingredient.restaurant_id == restaurant_id,
            )
        )

        await db.execute(
            delete(Restaurant).where(
                Restaurant.id == restaurant_id,
            )
        )

        await db.commit()


# ---------------------------------------------------------------------------
# Recipe API tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_recipe(client, db_session_factory):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    try:
        response = await client.post(
            "/recipes",
            json={
                "restaurant_id": str(restaurant_id),
                "name": "Margherita Pizza",
                "description": "Classic pizza recipe",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["restaurant_id"] == str(restaurant_id)
        assert data["name"] == "Margherita Pizza"
        assert data["description"] == "Classic pizza recipe"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )


@pytest.mark.anyio
async def test_list_recipes_returns_only_restaurant_recipes(
    client,
    db_session_factory,
):
    restaurant_id = uuid4()
    other_restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    await create_restaurant(
        db_session_factory,
        other_restaurant_id,
    )

    first_recipe_id = await create_recipe(
        db_session_factory,
        restaurant_id,
        name="Recipe One",
    )

    second_recipe_id = await create_recipe(
        db_session_factory,
        restaurant_id,
        name="Recipe Two",
    )

    await create_recipe(
        db_session_factory,
        other_restaurant_id,
        name="Other Restaurant Recipe",
    )

    try:
        response = await client.get(
            "/recipes",
            params={
                "restaurant_id": str(restaurant_id),
            },
        )

        assert response.status_code == 200

        data = response.json()

        recipe_ids = {
            recipe["id"]
            for recipe in data
        }

        assert recipe_ids == {
            str(first_recipe_id),
            str(second_recipe_id),
        }

        assert all(
            recipe["restaurant_id"]
            == str(restaurant_id)
            for recipe in data
        )

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )

        await cleanup_restaurant(
            db_session_factory,
            other_restaurant_id,
        )


@pytest.mark.anyio
async def test_get_recipe(client, db_session_factory):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    recipe_id = await create_recipe(
        db_session_factory,
        restaurant_id,
        name="Chicken Curry",
        description="API test curry",
    )

    try:
        response = await client.get(
            f"/recipes/{recipe_id}",
            params={
                "restaurant_id": str(restaurant_id),
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == str(recipe_id)
        assert data["restaurant_id"] == str(restaurant_id)
        assert data["name"] == "Chicken Curry"
        assert data["description"] == "API test curry"

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )


@pytest.mark.anyio
async def test_get_recipe_returns_404_for_wrong_restaurant(
    client,
    db_session_factory,
):
    restaurant_id = uuid4()
    other_restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    await create_restaurant(
        db_session_factory,
        other_restaurant_id,
    )

    recipe_id = await create_recipe(
        db_session_factory,
        restaurant_id,
        name="Private Recipe",
    )

    try:
        response = await client.get(
            f"/recipes/{recipe_id}",
            params={
                "restaurant_id": str(other_restaurant_id),
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Recipe not found"

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )

        await cleanup_restaurant(
            db_session_factory,
            other_restaurant_id,
        )


@pytest.mark.anyio
async def test_update_recipe(client, db_session_factory):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    recipe_id = await create_recipe(
        db_session_factory,
        restaurant_id,
        name="Old Recipe Name",
        description="Old description",
    )

    try:
        response = await client.patch(
            f"/recipes/{recipe_id}",
            params={
                "restaurant_id": str(restaurant_id),
            },
            json={
                "name": "Updated Recipe Name",
                "description": "Updated description",
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == str(recipe_id)
        assert data["name"] == "Updated Recipe Name"
        assert data["description"] == "Updated description"

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )


@pytest.mark.anyio
async def test_update_recipe_returns_404_when_not_found(
    client,
    db_session_factory,
):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    try:
        response = await client.patch(
            f"/recipes/{uuid4()}",
            params={
                "restaurant_id": str(restaurant_id),
            },
            json={
                "name": "Does Not Exist",
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Recipe not found"

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )


@pytest.mark.anyio
async def test_delete_recipe(client, db_session_factory):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    recipe_id = await create_recipe(
        db_session_factory,
        restaurant_id,
        name="Recipe To Delete",
    )

    try:
        response = await client.delete(
            f"/recipes/{recipe_id}",
            params={
                "restaurant_id": str(restaurant_id),
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["message"] == "Recipe deleted successfully"
        assert data["recipe_id"] == str(recipe_id)

        verify_response = await client.get(
            f"/recipes/{recipe_id}",
            params={
                "restaurant_id": str(restaurant_id),
            },
        )

        assert verify_response.status_code == 404

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )


# ---------------------------------------------------------------------------
# Recipe ingredient API tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_add_recipe_ingredient(
    client,
    db_session_factory,
):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    recipe_id = await create_recipe(
        db_session_factory,
        restaurant_id,
        name="Tomato Pasta",
    )

    ingredient_id = await create_ingredient(
        db_session_factory,
        restaurant_id,
        name="Tomato",
        unit="kg",
        cost_per_unit=Decimal("4.50"),
    )

    try:
        response = await client.post(
            f"/recipes/{recipe_id}/ingredients",
            params={
                "restaurant_id": str(restaurant_id),
            },
            json={
                "ingredient_id": str(ingredient_id),
                "quantity": 0.5,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["recipe_id"] == str(recipe_id)
        assert data["ingredient_id"] == str(ingredient_id)
        assert data["quantity"] == 0.5
        assert "id" in data

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )


@pytest.mark.anyio
async def test_add_recipe_ingredient_rejects_non_positive_quantity(
    client,
    db_session_factory,
):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    recipe_id = await create_recipe(
        db_session_factory,
        restaurant_id,
    )

    ingredient_id = await create_ingredient(
        db_session_factory,
        restaurant_id,
    )

    try:
        response = await client.post(
            f"/recipes/{recipe_id}/ingredients",
            params={
                "restaurant_id": str(restaurant_id),
            },
            json={
                "ingredient_id": str(ingredient_id),
                "quantity": 0,
            },
        )

        assert response.status_code == 422

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )


@pytest.mark.anyio
async def test_list_recipe_ingredients(
    client,
    db_session_factory,
):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    recipe_id = await create_recipe(
        db_session_factory,
        restaurant_id,
    )

    first_ingredient_id = await create_ingredient(
        db_session_factory,
        restaurant_id,
        name="Tomato",
        cost_per_unit=Decimal("4.00"),
    )

    second_ingredient_id = await create_ingredient(
        db_session_factory,
        restaurant_id,
        name="Basil",
        cost_per_unit=Decimal("8.00"),
    )

    await create_recipe_ingredient(
        db_session_factory,
        recipe_id,
        first_ingredient_id,
        quantity=Decimal("0.500"),
    )

    await create_recipe_ingredient(
        db_session_factory,
        recipe_id,
        second_ingredient_id,
        quantity=Decimal("0.050"),
    )

    try:
        response = await client.get(
            f"/recipes/{recipe_id}/ingredients",
            params={
                "restaurant_id": str(restaurant_id),
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert len(data) == 2

        returned_ingredient_ids = {
            item["ingredient_id"]
            for item in data
        }

        assert returned_ingredient_ids == {
            str(first_ingredient_id),
            str(second_ingredient_id),
        }

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )


@pytest.mark.anyio
async def test_update_recipe_ingredient(
    client,
    db_session_factory,
):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    recipe_id = await create_recipe(
        db_session_factory,
        restaurant_id,
    )

    ingredient_id = await create_ingredient(
        db_session_factory,
        restaurant_id,
    )

    recipe_ingredient_id = await create_recipe_ingredient(
        db_session_factory,
        recipe_id,
        ingredient_id,
        quantity=Decimal("0.500"),
    )

    try:
        response = await client.patch(
            (
                f"/recipes/{recipe_id}/ingredients/"
                f"{recipe_ingredient_id}"
            ),
            params={
                "restaurant_id": str(restaurant_id),
            },
            json={
                "quantity": 1.250,
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == str(recipe_ingredient_id)
        assert data["recipe_id"] == str(recipe_id)
        assert data["ingredient_id"] == str(ingredient_id)
        assert data["quantity"] == 1.25

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )


@pytest.mark.anyio
async def test_delete_recipe_ingredient(
    client,
    db_session_factory,
):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    recipe_id = await create_recipe(
        db_session_factory,
        restaurant_id,
    )

    ingredient_id = await create_ingredient(
        db_session_factory,
        restaurant_id,
    )

    recipe_ingredient_id = await create_recipe_ingredient(
        db_session_factory,
        recipe_id,
        ingredient_id,
    )

    try:
        response = await client.delete(
            (
                f"/recipes/{recipe_id}/ingredients/"
                f"{recipe_ingredient_id}"
            ),
            params={
                "restaurant_id": str(restaurant_id),
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert (
            data["message"]
            == "Recipe ingredient deleted successfully"
        )

        assert (
            data["recipe_ingredient_id"]
            == str(recipe_ingredient_id)
        )

        verify_response = await client.get(
            f"/recipes/{recipe_id}/ingredients",
            params={
                "restaurant_id": str(restaurant_id),
            },
        )

        assert verify_response.status_code == 200
        assert verify_response.json() == []

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )


# ---------------------------------------------------------------------------
# Food cost API tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_get_food_cost(
    client,
    db_session_factory,
):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    recipe_id = await create_recipe(
        db_session_factory,
        restaurant_id,
        name="Tomato Pasta",
    )

    tomato_id = await create_ingredient(
        db_session_factory,
        restaurant_id,
        name="Tomato",
        unit="kg",
        cost_per_unit=Decimal("4.00"),
    )

    cheese_id = await create_ingredient(
        db_session_factory,
        restaurant_id,
        name="Cheese",
        unit="kg",
        cost_per_unit=Decimal("10.00"),
    )

    await create_recipe_ingredient(
        db_session_factory,
        recipe_id,
        tomato_id,
        quantity=Decimal("0.500"),
    )

    await create_recipe_ingredient(
        db_session_factory,
        recipe_id,
        cheese_id,
        quantity=Decimal("0.200"),
    )

    try:
        response = await client.get(
            f"/recipes/{recipe_id}/food-cost",
            params={
                "restaurant_id": str(restaurant_id),
            },
        )

        assert response.status_code == 200

        data = response.json()

        assert data["recipe_id"] == str(recipe_id)
        assert data["recipe_name"] == "Tomato Pasta"

        assert data["food_cost"] == 4.0

        
        assert len(data["breakdown"]) == 2

        breakdown = {
            item["ingredient"]: item
            for item in data["breakdown"]
        }

        assert "Tomato" in breakdown
        assert "Cheese" in breakdown

        assert breakdown["Tomato"]["quantity"] == 0.5
        assert breakdown["Tomato"]["cost_per_unit"] == 4.0
        assert breakdown["Tomato"]["total_cost"] == 2.0

        assert breakdown["Cheese"]["quantity"] == 0.2
        assert breakdown["Cheese"]["cost_per_unit"] == 10.0
        assert breakdown["Cheese"]["total_cost"] == 2.0



    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )


@pytest.mark.anyio
async def test_get_food_cost_returns_404_for_missing_recipe(
    client,
    db_session_factory,
):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    try:
        response = await client.get(
            f"/recipes/{uuid4()}/food-cost",
            params={
                "restaurant_id": str(restaurant_id),
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Recipe not found"

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_recipe_rejects_empty_name(
    client,
    db_session_factory,
):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    try:
        response = await client.post(
            "/recipes",
            json={
                "restaurant_id": str(restaurant_id),
                "name": "",
            },
        )

        assert response.status_code == 422

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )


@pytest.mark.anyio
async def test_create_recipe_rejects_missing_restaurant_id(
    client,
):
    response = await client.post(
        "/recipes",
        json={
            "name": "Recipe Without Restaurant",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_add_recipe_ingredient_rejects_invalid_quantity(
    client,
    db_session_factory,
):
    restaurant_id = uuid4()

    await create_restaurant(
        db_session_factory,
        restaurant_id,
    )

    recipe_id = await create_recipe(
        db_session_factory,
        restaurant_id,
    )

    ingredient_id = await create_ingredient(
        db_session_factory,
        restaurant_id,
    )

    try:
        response = await client.post(
            f"/recipes/{recipe_id}/ingredients",
            params={
                "restaurant_id": str(restaurant_id),
            },
            json={
                "ingredient_id": str(ingredient_id),
                "quantity": -1,
            },
        )

        assert response.status_code == 422

    finally:
        await cleanup_restaurant(
            db_session_factory,
            restaurant_id,
        )

