import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.recipe import Recipe
    from app.models.restaurant_memory import RestaurantMemory
    from app.models.restaurant_insight import RestaurantInsight


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    recipes: Mapped[list["Recipe"]] = relationship(
        "Recipe",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )

    memories: Mapped[list["RestaurantMemory"]] = relationship(
        "RestaurantMemory",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )
    insights: Mapped[list["RestaurantInsight"]] = relationship(
        "RestaurantInsight",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )