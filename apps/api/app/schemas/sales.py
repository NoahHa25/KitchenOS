from decimal import Decimal

from pydantic import BaseModel


class SalesSummaryResponse(BaseModel):
    total_orders: int
    total_revenue: Decimal