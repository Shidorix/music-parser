# Backend Status

Backend готов для MVP и перехода к frontend-разработке.

## Реализовано

- NLP pipeline: normalization, language detection, transliteration, pattern detection.
- Parser evaluation на размеченном датасете.
- Fuzzy matching: Levenshtein и Jaro-Winkler.
- Matcher evaluation и сравнение алгоритмов.
- Search layer: demo provider, Spotify provider, YouTube provider.
- Retry/backoff для transient ошибок Spotify/YouTube.
- FastAPI API v1 со стандартным response envelope.
- Anonymous sessions для frontend localStorage flow.
- Playlist persistence на SQLAlchemy async.
- Alembic migrations.
- Playlist management: create, read, list, rename, delete.
- Playlist item management: manual review, delete item.
- Analytics endpoint для качества плейлиста.
- Export endpoint: JSON, CSV, M3U.
- CORS для локального frontend.
- Dockerfile и Docker Compose для backend + PostgreSQL.
- Русскоязычный чеклист ручного тестирования backend.

## Проверено

Автоматические тесты:

```text
python -m pytest backend
96 passed
```

Linting:

```text
python -m ruff check backend migrations
All checks passed
```

Formatting:

```text
python -m black --check backend migrations
102 files would be left unchanged
```

Docker Compose config:

```text
docker compose config
OK
```

Docker image build не был проверен в этой среде, потому что Docker Desktop daemon
не запущен:

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

Research commands:

```text
python -m backend.core.parser.evaluation datasets\parser\labeled_tracks.jsonl
total=10 artist_accuracy=1.0000 title_accuracy=1.0000 pattern_accuracy=1.0000 exact_match_accuracy=1.0000
```

```text
python -m backend.core.matcher.evaluation --compare-all
algorithm       total   k   top_1_accuracy  top_k_accuracy  ambiguous_count
jaro_winkler    14      3   0.7857          1.0000          7
levenshtein     14      3   0.7143          1.0000          6
```

## Необязательный Backlog

Эти задачи не блокируют frontend MVP:

- Spotify OAuth flow вместо ручного access token через env.
- Более строгая авторизация вместо anonymous sessions.
- CI pipeline для автоматического запуска tests/lint/format.
- Structured logging, request ids, metrics.
- Расширение research datasets и notebooks для магистерской главы.
