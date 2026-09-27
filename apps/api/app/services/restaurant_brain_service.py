from uuid import UUID

from app.models.restaurant_insight import RestaurantInsight
from app.repositories.restaurant_insight_repository import (
    RestaurantInsightRepository,
)
from app.schemas.restaurant_insight import (
    RestaurantInsightCreate,
    RestaurantInsightUpdate,
)


class RestaurantBrainService:
    def __init__(
        self,
        repository: RestaurantInsightRepository,
    ):
        self.repository = repository

    async def create_insight(
        self,
        restaurant_id: UUID,
        data: RestaurantInsightCreate,
    ) -> RestaurantInsight:
        existing_insights = await self.repository.list(
            restaurant_id=restaurant_id,
            status="active",
        )

        for insight in existing_insights:
            if (
                insight.insight_type == data.insight_type
                and insight.title == data.title
            ):
                return insight

        return await self.repository.create(
            restaurant_id=restaurant_id,
            data=data,
        )

    async def get_insight(
        self,
        restaurant_id: UUID,
        insight_id: UUID,
    ) -> RestaurantInsight | None:
        return await self.repository.get_by_id(
            restaurant_id=restaurant_id,
            insight_id=insight_id,
        )

    async def list_insights(
        self,
        restaurant_id: UUID,
        status: str | None = "active",
    ) -> list[RestaurantInsight]:
        return await self.repository.list(
            restaurant_id=restaurant_id,
            status=status,
        )

    async def update_insight(
        self,
        restaurant_id: UUID,
        insight_id: UUID,
        data: RestaurantInsightUpdate,
    ) -> RestaurantInsight | None:
        return await self.repository.update(
            restaurant_id=restaurant_id,
            insight_id=insight_id,
            data=data,
        )

    async def resolve_insight(
        self,
        restaurant_id: UUID,
        insight_id: UUID,
    ) -> RestaurantInsight | None:
        insight = await self.repository.get_by_id(
            restaurant_id=restaurant_id,
            insight_id=insight_id,
        )

        if insight is None:
            return None

        return await self.repository.update(
            restaurant_id=restaurant_id,
            insight_id=insight_id,
            data=RestaurantInsightUpdate(
                status="resolved",
            ),
        )