from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.models.restaurant_memory import RestaurantMemory
from app.models.restaurant_insight import RestaurantInsight
from app.repositories.restaurant_memory import RestaurantMemoryRepository
from app.repositories.inventory_movement_repository import (
    InventoryMovementRepository,
)
from app.schemas.restaurant_insight import RestaurantInsightCreate
from app.services.restaurant_brain_detector import (
    detect_repeated_problem,
)
from app.services.restaurant_brain_service import (
    RestaurantBrainService,
)



class RestaurantBrainAnalysisService:
    def __init__(
        self,
        inventory_repository: InventoryMovementRepository,
        brain_service: RestaurantBrainService,
        memory_repository: RestaurantMemoryRepository,
    ):
        self.inventory_repository = inventory_repository
        self.brain_service = brain_service
        self.memory_repository = memory_repository

    async def detect_repeated_waste(
        self,
        restaurant_id: UUID,
        lookback_days: int = 30,
        threshold: int = 3,
    ) -> list[RestaurantInsight]:
        now = datetime.now(timezone.utc)
        created_after = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        movements = (
            await self.inventory_repository.get_restaurant_movements(
                restaurant_id=restaurant_id,
                movement_type="waste",
                created_after=created_after,
            )
        )

        ingredient_counts: dict[UUID, int] = {}
        ingredient_names: dict[UUID, str] = {}

        for movement in movements:
            ingredient = movement.ingredient

            ingredient_counts[movement.ingredient_id] = (
                ingredient_counts.get(movement.ingredient_id, 0) + 1
            )

            ingredient_names[movement.ingredient_id] = ingredient.name

        insights: list[RestaurantInsight] = []

        for ingredient_id, occurrence_count in ingredient_counts.items():
            ingredient_name = ingredient_names[ingredient_id]

            result = detect_repeated_problem(
                problem_name=f"{ingredient_name} waste",
                occurrence_count=occurrence_count,
                time_window_days=lookback_days,
                threshold=threshold,
            )

            if not result.detected:
                continue

            insight = await self.brain_service.create_insight(
                restaurant_id=restaurant_id,
                data=RestaurantInsightCreate(
                    insight_type="repeated_problem",
                    title=result.title,
                    description=result.description,
                    severity=result.severity,
                    confidence=result.confidence,
                    evidence=result.evidence,
                ),
            )

            insights.append(insight)

        return insights
    
    
    async def detect_repeated_memory_problems(
        self,
        *,
        restaurant_id: UUID,
        lookback_days: int = 30,
        threshold: int = 3,
    ) -> list[RestaurantInsight]:
        created_after = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        memories = await self.memory_repository.list_recent(
            restaurant_id=restaurant_id,
            created_after=created_after,
        )

        grouped: dict[tuple[str, str], list[RestaurantMemory]] = {}

        for memory in memories:
            key = (
                memory.memory_type,
                memory.title.strip().lower(),
            )

            grouped.setdefault(key, []).append(memory)

        insights: list[RestaurantInsight] = []

        for (memory_type, normalized_title), matching_memories in grouped.items():
            occurrence_count = len(matching_memories)

            detection = detect_repeated_problem(
                problem_name=matching_memories[0].title,
                occurrence_count=occurrence_count,
                time_window_days=lookback_days,
                threshold=threshold,
            )

            if not detection.detected:
                continue

            insight = await self.brain_service.create_insight(
                restaurant_id=restaurant_id,
                data=RestaurantInsightCreate(
                    insight_type="repeated_problem",
                    title=detection.title,
                    description=detection.description,
                    severity=detection.severity,
                    confidence=detection.confidence,
                    evidence=detection.evidence,
                ),
            )

            insights.append(insight)

        return insights