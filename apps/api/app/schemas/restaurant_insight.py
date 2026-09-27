from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


InsightType = Literal[
    "inventory_shortage",
    "supplier_delay",
    "sales_anomaly",
    "waste_spike",
    "food_cost_change",
    "equipment_issue",
    "repeated_problem",
]

InsightSeverity = Literal[
    "low",
    "medium",
    "high",
    "critical",
]

InsightConfidence = Literal[
    "low",
    "medium",
    "high",
]

InsightStatus = Literal[
    "active",
    "resolved",
]


class RestaurantInsightCreate(BaseModel):
    insight_type: InsightType
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    severity: InsightSeverity = "medium"
    confidence: InsightConfidence = "medium"
    evidence: str | None = None


class RestaurantInsightUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        min_length=1,
    )

    severity: InsightSeverity | None = None
    confidence: InsightConfidence | None = None
    status: InsightStatus | None = None
    evidence: str | None = None
    resolved_at: datetime | None = None


class RestaurantInsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    insight_type: InsightType
    title: str
    description: str
    severity: InsightSeverity
    confidence: InsightConfidence
    status: InsightStatus
    evidence: str | None
    created_at: datetime
    resolved_at: datetime | None