from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RecipeIngredientCreate(BaseModel):
    ingredient_id: UUID
    quantity: float = Field(gt=0)


class RecipeIngredientUpdate(BaseModel):
    quantity: float = Field(gt=0)


class RecipeIngredientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recipe_id: UUID
    ingredient_id: UUID
    quantity: float
    