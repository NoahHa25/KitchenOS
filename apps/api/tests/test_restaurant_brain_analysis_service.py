from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.ingredient import Ingredient
from app.models.restaurant import Restaurant
from app.repositories.inventory_movement_repository import (
    InventoryMovementRepository,
)
from app.repositories.restaurant_insight_repository import (
    RestaurantInsightRepository,
)
from app.services.restaurant_brain_analysis_service import (
    RestaurantBrainAnalysisService,
)
from app.services.restaurant_brain_service import (
    RestaurantBrainService,
)

from app.repositories.restaurant_memory import RestaurantMemoryRepository


@pytest.mark.anyio
async def test_detect_repeated_waste_from_real_inventory_movements(
    db_session,
):
    restaurant = Restaurant(
        name="Brain Test Restaurant",
        slug=f"brain-test-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    ingredient = Ingredient(
        restaurant_id=restaurant.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    db_session.add(ingredient)
    await db_session.flush()

    inventory_repository = InventoryMovementRepository(db_session)
    memory_repository = RestaurantMemoryRepository(db_session)
    insight_repository = RestaurantInsightRepository(db_session)
    brain_service = RestaurantBrainService(insight_repository)

    analysis_service = RestaurantBrainAnalysisService(
        inventory_repository=inventory_repository,
        memory_repository=memory_repository,
        brain_service=brain_service,
    )

    for _ in range(4):
        movement = await inventory_repository.create(
            ingredient_id=ingredient.id,
            movement_type="waste",
            quantity=Decimal("1.000"),
            unit_cost=Decimal("2.50"),
            reason="Spoilage",
        )

        movement.created_at = datetime.now(timezone.utc)

    await db_session.flush()

    insights = await analysis_service.detect_repeated_waste(
        restaurant_id=restaurant.id,
        lookback_days=30,
        threshold=3,
    )

    assert len(insights) == 1

    insight = insights[0]

    assert insight.restaurant_id == restaurant.id
    assert insight.insight_type == "repeated_problem"
    assert insight.title == "Tomatoes waste is recurring"
    assert (
        insight.description
        == "Tomatoes waste occurred 4 times during the last 30 days."
    )
    assert insight.severity == "high"
    assert insight.confidence == "medium"
    assert (
        insight.evidence
        == "4 occurrences during the last 30 days."
    )


@pytest.mark.anyio
async def test_repeated_waste_below_threshold_creates_no_insight(
    db_session,
):
    restaurant = Restaurant(
        name="Brain Test Restaurant",
        slug=f"brain-test-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    ingredient = Ingredient(
        restaurant_id=restaurant.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    db_session.add(ingredient)
    await db_session.flush()


    inventory_repository = InventoryMovementRepository(db_session)
    memory_repository = RestaurantMemoryRepository(db_session)
    insight_repository = RestaurantInsightRepository(db_session)
    brain_service = RestaurantBrainService(insight_repository)
    

    analysis_service = RestaurantBrainAnalysisService(
        inventory_repository=inventory_repository,
        brain_service=brain_service,
        memory_repository=memory_repository,
    )

    for _ in range(2):
        await inventory_repository.create(
            ingredient_id=ingredient.id,
            movement_type="waste",
            quantity=Decimal("1.000"),
            unit_cost=Decimal("2.50"),
            reason="Spoilage",
        )

    insights = await analysis_service.detect_repeated_waste(
        restaurant_id=restaurant.id,
        lookback_days=30,
        threshold=3,
    )

    assert insights == []


@pytest.mark.anyio
async def test_waste_outside_lookback_window_is_ignored(
    db_session,
):
    restaurant = Restaurant(
        name="Brain Test Restaurant",
        slug=f"brain-test-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    ingredient = Ingredient(
        restaurant_id=restaurant.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    db_session.add(ingredient)
    await db_session.flush()

    inventory_repository = InventoryMovementRepository(db_session)
    memory_repository = RestaurantMemoryRepository(db_session)
    insight_repository = RestaurantInsightRepository(db_session)
    brain_service = RestaurantBrainService(insight_repository)

    analysis_service = RestaurantBrainAnalysisService(
        inventory_repository=inventory_repository,
        memory_repository=memory_repository,
        brain_service=brain_service,
    )

    old_date = datetime.now(timezone.utc) - timedelta(days=60)

    for _ in range(4):
        movement = await inventory_repository.create(
            ingredient_id=ingredient.id,
            movement_type="waste",
            quantity=Decimal("1.000"),
            unit_cost=Decimal("2.50"),
            reason="Old spoilage",
        )

        movement.created_at = old_date

    await db_session.flush()

    insights = await analysis_service.detect_repeated_waste(
        restaurant_id=restaurant.id,
        lookback_days=30,
        threshold=3,
    )

    assert insights == []


@pytest.mark.anyio
async def test_other_movement_types_are_ignored(
    db_session,
):
    restaurant = Restaurant(
        name="Brain Test Restaurant",
        slug=f"brain-test-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    ingredient = Ingredient(
        restaurant_id=restaurant.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    db_session.add(ingredient)
    await db_session.flush()

    inventory_repository = InventoryMovementRepository(db_session)
    memory_repository = RestaurantMemoryRepository(db_session)
    insight_repository = RestaurantInsightRepository(db_session)
    brain_service = RestaurantBrainService(insight_repository)

    analysis_service = RestaurantBrainAnalysisService(
        inventory_repository=inventory_repository,
        memory_repository=memory_repository,
        brain_service=brain_service,
    )

    for _ in range(5):
        await inventory_repository.create(
            ingredient_id=ingredient.id,
            movement_type="purchase",
            quantity=Decimal("10.000"),
            unit_cost=Decimal("2.50"),
            reason="Supplier delivery",
        )

    insights = await analysis_service.detect_repeated_waste(
        restaurant_id=restaurant.id,
        lookback_days=30,
        threshold=3,
    )

    assert insights == []


@pytest.mark.anyio
async def test_multiple_ingredients_generate_separate_insights(
    db_session,
):
    restaurant = Restaurant(
        name="Brain Test Restaurant",
        slug=f"brain-test-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    tomatoes = Ingredient(
        restaurant_id=restaurant.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    onions = Ingredient(
        restaurant_id=restaurant.id,
        name="Onions",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=1.50,
    )

    db_session.add_all([tomatoes, onions])
    await db_session.flush()

    inventory_repository = InventoryMovementRepository(db_session)
    memory_repository = RestaurantMemoryRepository(db_session)
    insight_repository = RestaurantInsightRepository(db_session)
    brain_service = RestaurantBrainService(insight_repository)

    analysis_service = RestaurantBrainAnalysisService(
        inventory_repository=inventory_repository,
        memory_repository=memory_repository,
        brain_service=brain_service,
    )

    for _ in range(3):
        await inventory_repository.create(
            ingredient_id=tomatoes.id,
            movement_type="waste",
            quantity=Decimal("1.000"),
            unit_cost=Decimal("2.50"),
            reason="Spoilage",
        )

    for _ in range(5):
        await inventory_repository.create(
            ingredient_id=onions.id,
            movement_type="waste",
            quantity=Decimal("1.000"),
            unit_cost=Decimal("1.50"),
            reason="Spoilage",
        )

    insights = await analysis_service.detect_repeated_waste(
        restaurant_id=restaurant.id,
        lookback_days=30,
        threshold=3,
    )

    assert len(insights) == 2

    titles = {insight.title for insight in insights}

    assert "Tomatoes waste is recurring" in titles
    assert "Onions waste is recurring" in titles
    
    
@pytest.mark.anyio
async def test_repeated_analysis_does_not_create_duplicate_insights(
    db_session,
):
    restaurant = Restaurant(
        name="Brain Test Restaurant",
        slug=f"brain-test-{uuid4()}",
    )

    db_session.add(restaurant)
    await db_session.flush()

    ingredient = Ingredient(
        restaurant_id=restaurant.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    db_session.add(ingredient)
    await db_session.flush()

    inventory_repository = InventoryMovementRepository(db_session)
    memory_repository = RestaurantMemoryRepository(db_session)
    insight_repository = RestaurantInsightRepository(db_session)
    brain_service = RestaurantBrainService(insight_repository)

    analysis_service = RestaurantBrainAnalysisService(
        inventory_repository=inventory_repository,
        memory_repository=memory_repository,
        brain_service=brain_service,
    )

    for _ in range(4):
        await inventory_repository.create(
            ingredient_id=ingredient.id,
            movement_type="waste",
            quantity=Decimal("1.000"),
            unit_cost=Decimal("2.50"),
            reason="Spoilage",
        )

    first_run = await analysis_service.detect_repeated_waste(
        restaurant_id=restaurant.id,
        lookback_days=30,
        threshold=3,
    )

    second_run = await analysis_service.detect_repeated_waste(
        restaurant_id=restaurant.id,
        lookback_days=30,
        threshold=3,
    )

    assert len(first_run) == 1
    assert len(second_run) == 1

    assert first_run[0].id == second_run[0].id

    all_insights = await insight_repository.list(
        restaurant_id=restaurant.id,
        status="active",
    )

    assert len(all_insights) == 1


@pytest.mark.anyio
async def test_analysis_is_isolated_between_restaurants(
    db_session,
):
    restaurant_a = Restaurant(
        name="Restaurant A",
        slug=f"restaurant-a-{uuid4()}",
    )

    restaurant_b = Restaurant(
        name="Restaurant B",
        slug=f"restaurant-b-{uuid4()}",
    )

    db_session.add_all([restaurant_a, restaurant_b])
    await db_session.flush()

    tomatoes_a = Ingredient(
        restaurant_id=restaurant_a.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    tomatoes_b = Ingredient(
        restaurant_id=restaurant_b.id,
        name="Tomatoes",
        unit="kg",
        current_stock=10,
        minimum_stock=3,
        cost_per_unit=2.50,
    )

    db_session.add_all([tomatoes_a, tomatoes_b])
    await db_session.flush()

    inventory_repository = InventoryMovementRepository(db_session)
    memory_repository = RestaurantMemoryRepository(db_session)
    insight_repository = RestaurantInsightRepository(db_session)
    brain_service = RestaurantBrainService(insight_repository)

    analysis_service = RestaurantBrainAnalysisService(
        inventory_repository=inventory_repository,
        memory_repository=memory_repository,
        brain_service=brain_service,
    )

    for _ in range(4):
        await inventory_repository.create(
            ingredient_id=tomatoes_a.id,
            movement_type="waste",
            quantity=Decimal("1.000"),
            unit_cost=Decimal("2.50"),
            reason="Restaurant A spoilage",
        )

    for _ in range(2):
        await inventory_repository.create(
            ingredient_id=tomatoes_b.id,
            movement_type="waste",
            quantity=Decimal("1.000"),
            unit_cost=Decimal("2.50"),
            reason="Restaurant B spoilage",
        )

    insights_a = await analysis_service.detect_repeated_waste(
        restaurant_id=restaurant_a.id,
        lookback_days=30,
        threshold=3,
    )

    insights_b = await analysis_service.detect_repeated_waste(
        restaurant_id=restaurant_b.id,
        lookback_days=30,
        threshold=3,
    )

    assert len(insights_a) == 1
    assert insights_a[0].restaurant_id == restaurant_a.id

    assert insights_b == []