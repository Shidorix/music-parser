# Database Migrations

Alembic migrations for the Playlist Parser backend.

Useful commands:

```bash
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "describe change"
```

The database URL is read from `PLAYLIST_PARSER_DATABASE_URL`.
