import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.mark.asyncio
async def test_search_endpoint_returns_demo_candidates() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/search",
            json={
                "query": "Daft Punk - Around the World",
                "limit_per_source": 1,
            },
        )

    payload = response.json()

    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["meta"] == {"total": 1, "page": 0}
    assert payload["data"]["candidates"][0]["track_id"] == (
        "demo:daft-punk-around-the-world"
    )
    assert payload["data"]["source_reports"][0] == {
        "source": "demo",
        "status": "success",
        "candidate_count": 1,
        "error_code": None,
        "error_message": None,
    }


@pytest.mark.asyncio
async def test_search_endpoint_validates_request_body() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/search",
            json={"query": "", "limit_per_source": 1},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
