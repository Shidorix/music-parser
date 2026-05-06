import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.mark.asyncio
async def test_parse_endpoint_returns_parser_metadata() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/parse",
            json={
                "raw_lines": [
                    "Daft Punk - Around the World",
                    "Кино - Группа крови",
                ]
            },
        )

    payload = response.json()

    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["meta"] == {"total": 2, "page": 0}
    assert payload["data"]["items"][0]["artist"] == "daft punk"
    assert payload["data"]["items"][0]["title"] == "around the world"
    assert payload["data"]["items"][1]["language"] == "ru"
    assert payload["data"]["items"][1]["transliteration_candidates"][0]["text"] == (
        "kino - gruppa krovi"
    )


@pytest.mark.asyncio
async def test_parse_endpoint_validates_request_body() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/parse", json={"raw_lines": []})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
