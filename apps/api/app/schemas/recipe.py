from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecipeCreate(BaseModel):
    restaurant_id: UUID

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    selling_price: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        decimal_places=2,
        max_digits=10,
    )

    portion_size: float = Field(
        default=1.0,
        gt=0,
    )

    portion_unit: str = Field(
        default="portion",
        min_length=1,
        max_length=20,
    )

    is_active: bool = Field(
        default=True,
    )


class RecipeUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    selling_price: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        max_digits=10,
    )

    portion_size: float | None = Field(
        default=None,
        gt=0,
    )

    portion_unit: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    is_active: bool | None = Field(
        default=None,
    )


class RecipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    restaurant_id: UUID
    name: str
    description: str | None

    selling_price: Decimal
    portion_size: float
    portion_unit: str
    is_active: bool