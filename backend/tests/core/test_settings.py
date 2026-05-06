from backend.core.settings import Settings


def test_parses_cors_allowed_origins() -> None:
    settings = Settings(
        cors_allowed_origins=" http://localhost:5173, http://127.0.0.1:5173 ,,"
    )

    assert settings.parsed_cors_allowed_origins() == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
