from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant_insight import RestaurantInsight
from app.schemas.restaurant_insight import (
    RestaurantInsightCreate,
    RestaurantInsightUpdate,
)


class RestaurantInsightRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        restaurant_id: UUID,
        data: RestaurantInsightCreate,
    ) -> RestaurantInsight:
        insight = RestaurantInsight(
            restaurant_id=restaurant_id,
            insight_type=data.insight_type,
            title=data.title,
            description=data.description,
            severity=data.severity,
            confidence=data.confidence,
            evidence=data.evidence,
        )

        self.db.add(insight)
        await self.db.flush()
        await self.db.refresh(insight)

        return insight

    async def get_by_id(
        self,
        restaurant_id: UUID,
        insight_id: UUID,
    ) -> RestaurantInsight | None:
        result = await self.db.execute(
            select(RestaurantInsight).where(
                RestaurantInsight.id == insight_id,
                RestaurantInsight.restaurant_id == restaurant_id,
            )
        )

        return result.scalar_one_or_none()

    async def list(
        self,
        restaurant_id: UUID,
        status: str | None = None,
    ) -> list[RestaurantInsight]:
        query = select(RestaurantInsight).where(
            RestaurantInsight.restaurant_id == restaurant_id,
        )

        if status is not None:
            query = query.where(
                RestaurantInsight.status == status,
            )

        query = query.order_by(
            RestaurantInsight.created_at.desc(),
        )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def update(
        self,
        restaurant_id: UUID,
        insight_id: UUID,
        data: RestaurantInsightUpdate,
    ) -> RestaurantInsight | None:
        insight = await self.get_by_id(
            restaurant_id=restaurant_id,
            insight_id=insight_id,
        )

        if insight is None:
            return None

        update_data = data.model_dump(
            exclude_unset=True,
        )

        for field, value in update_data.items():
            setattr(insight, field, value)

        await self.db.flush()
        await self.db.refresh(insight)

        return insight