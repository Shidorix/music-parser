from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from backend.core.settings import get_settings


def test_alembic_upgrade_and_downgrade_create_expected_tables(
    monkeypatch,
) -> None:
    artifact_dir = Path(".tmp")
    artifact_dir.mkdir(exist_ok=True)
    database_path = artifact_dir / f"migration_smoke_{uuid4().hex}.db"

    try:
        database_url = f"sqlite+aiosqlite:///{database_path.resolve().as_posix()}"
        sync_database_url = f"sqlite:///{database_path.resolve().as_posix()}"

        monkeypatch.setenv("PLAYLIST_PARSER_DATABASE_URL", database_url)
        get_settings.cache_clear()

        config = Config("alembic.ini")

        command.upgrade(config, "head")
        assert _table_names(sync_database_url) == [
            "alembic_version",
            "playlist_items",
            "playlists",
            "user_sessions",
        ]

        command.downgrade(config, "base")
        assert _table_names(sync_database_url) == ["alembic_version"]
    finally:
        get_settings.cache_clear()
        database_path.unlink(missing_ok=True)


def _table_names(database_url: str) -> list[str]:
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            return sorted(inspect(connection).get_table_names())
    finally:
        engine.dispose()
