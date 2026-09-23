from uuid import UUID

from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    restaurant_id: UUID
    query: str = Field(min_length=1)


class AssistantResponse(BaseModel):
    intent: str
    answer: str