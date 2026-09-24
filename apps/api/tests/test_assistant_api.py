from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_assistant_endpoint_is_available():
    restaurant_id = uuid4()

    payload = {
        "restaurant_id": str(restaurant_id),
        "query": "What should we buy today?",
    }

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/assistant",
            json=payload,
        )

    assert response.status_code == 200

    data = response.json()

    assert "intent" in data
    assert "answer" in data
