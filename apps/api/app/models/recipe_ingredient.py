from uuid import uuid4

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    __table_args__ = (
        UniqueConstraint(
            "recipe_id",
            "ingredient_id",
            name="uq_recipe_ingredient",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    recipe_id: Mapped[UUID] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
    )

    ingredient_id: Mapped[UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"),
        nullable=False,
    )

    quantity: Mapped[float] = mapped_column(
        Numeric(10, 3),
        nullable=False,
    )

    recipe: Mapped["Recipe"] = relationship(
        "Recipe",
        back_populates="ingredients",
    )

    ingredient: Mapped["Ingredient"] = relationship("Ingredient")