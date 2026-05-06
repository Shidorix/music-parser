import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.mark.asyncio
async def test_parse_and_match_endpoint_returns_standard_response() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/parse-and-match",
            json={
                "raw_lines": [
                    "Daft Punk - Around the World",
                    "Кино - Группа крови",
                ],
                "match_limit": 1,
            },
        )

    payload = response.json()

    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["meta"] == {"total": 2, "page": 0}
    assert payload["data"]["total"] == 2
    assert payload["data"]["items"][0]["match_result"]["matches"][0]["track_id"] == (
        "demo:daft-punk-around-the-world"
    )
    assert payload["data"]["items"][1]["match_result"]["matches"][0]["track_id"] == (
        "demo:kino-gruppa-krovi"
    )


@pytest.mark.asyncio
async def test_parse_and_match_endpoint_validates_request_body() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/parse-and-match",
            json={"raw_lines": [], "match_limit": 1},
        )

    assert response.status_code == 422
    assert response.json() == {
        "data": None,
        "meta": None,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
        },
    }
