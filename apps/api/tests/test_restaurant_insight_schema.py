import pytest
from pydantic import ValidationError

from app.schemas.restaurant_insight import (
    RestaurantInsightCreate,
    RestaurantInsightUpdate,
)


def test_create_insight_accepts_valid_data():
    insight = RestaurantInsightCreate(
        insight_type="inventory_shortage",
        title="Tomato shortage detected",
        description="Tomatoes reached minimum stock.",
        severity="high",
        confidence="high",
        evidence="Stock reached minimum level 4 times.",
    )

    assert insight.insight_type == "inventory_shortage"
    assert insight.severity == "high"
    assert insight.confidence == "high"


def test_create_insight_defaults():
    insight = RestaurantInsightCreate(
        insight_type="repeated_problem",
        title="Recurring issue",
        description="The same issue happened repeatedly.",
    )

    assert insight.severity == "medium"
    assert insight.confidence == "medium"


def test_invalid_insight_type_is_rejected():
    with pytest.raises(ValidationError):
        RestaurantInsightCreate(
            insight_type="random_problem",
            title="Invalid",
            description="Invalid insight type.",
        )


def test_invalid_severity_is_rejected():
    with pytest.raises(ValidationError):
        RestaurantInsightCreate(
            insight_type="inventory_shortage",
            title="Invalid severity",
            description="Invalid severity.",
            severity="extreme",
        )


def test_update_allows_partial_changes():
    update = RestaurantInsightUpdate(
        severity="critical",
        status="resolved",
    )

    assert update.severity == "critical"
    assert update.status == "resolved"
    assert update.title is None