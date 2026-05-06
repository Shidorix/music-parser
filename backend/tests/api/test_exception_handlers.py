import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.core.exceptions import AppException
from backend.main import create_app


@pytest.mark.asyncio
async def test_app_exception_handler_returns_standard_response() -> None:
    app = create_app()

    @app.get("/raise-app-exception")
    async def raise_app_exception() -> None:
        raise AppException(
            code="TEST_ERROR",
            message="Expected test error.",
            status_code=409,
        )

    response = await _get(app, "/raise-app-exception")

    assert response.status_code == 409
    assert response.json() == {
        "data": None,
        "meta": None,
        "error": {
            "code": "TEST_ERROR",
            "message": "Expected test error.",
        },
    }


async def _get(app: FastAPI, path: str):
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)
