# Music Parser

Full-stack приложение для разбора неструктурированных списков музыкальных
треков, поиска совпадений в музыкальных каталогах и сохранения результата как
плейлист.

Проект разрабатывается как практическая часть магистерской работы: внутри есть
измеримый NLP pipeline, несколько алгоритмов fuzzy matching, labeled datasets и
CLI-команды для сравнения качества.

## Что Уже Реализовано

- Backend на FastAPI с API v1 и единым response envelope.
- NLP pipeline: normalization, language detection, transliteration, pattern detection.
- Parser для строк вида `Artist - Title`, списков с нумерацией и смешанных RU/EN вводов.
- Fuzzy matching: Levenshtein baseline, Jaro-Winkler и hybrid matcher.
- Explainability: parse/match результаты возвращают confidence, source, algorithm и explanation.
- Domain aliases для частых музыкальных кейсов, например `цой -> Kino`.
- Demo catalog для локальной проверки без внешних API.
- Интеграции Spotify Web API и YouTube Data API v3 через optional env-настройки.
- Anonymous sessions для frontend flow.
- Playlist CRUD: создание, просмотр, список по session, переименование, удаление.
- Manual review: подтверждение или ручное исправление uncertain matches.
- Analytics endpoint: uncertain count, average score, source counts, algorithm counts.
- Export playlist в JSON, CSV и M3U.
- SQLite для локальной разработки, PostgreSQL через Docker Compose.
- Frontend на React + TypeScript + Vite + Bun.

## Tech Stack

Backend:

- Python 3.11+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x async
- Alembic
- SQLite locally
- PostgreSQL for Docker/production-like setup
- pytest, pytest-asyncio, httpx, respx
- Ruff, Black

Frontend:

- React 19
- TypeScript strict mode
- Vite
- Bun
- Lucide React

## Структура Проекта

```text
backend/              FastAPI app, core logic, integrations, tests
datasets/             labeled examples for parser and matcher evaluation
docs/                 detailed Russian testing and usage guides
frontend/             React TypeScript frontend
migrations/           Alembic migrations
docker-compose.yml    backend + PostgreSQL setup
pyproject.toml        Python package, dependencies, tooling
```

## Быстрый Запуск Backend

Установить зависимости:

```bash
python -m pip install -e ".[dev]"
```

Создать `.env`:

```bash
cp .env.example .env
```

На Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Применить миграции:

```bash
python -m alembic upgrade head
```

Запустить API:

```bash
python -m uvicorn backend.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Быстрый Запуск Frontend

```bash
cd frontend
bun install
bun run dev
```

Frontend по умолчанию открывается здесь:

```text
http://127.0.0.1:5173
```

API base URL по умолчанию:

```text
http://127.0.0.1:8000/api/v1
```

Для полноценной работы UI backend должен быть запущен отдельно.

## Docker Compose

Поднять backend и PostgreSQL:

```bash
docker compose up --build
```

Остановить:

```bash
docker compose down
```

Остановить и удалить PostgreSQL volume:

```bash
docker compose down -v
```

Для обычной локальной разработки Docker не обязателен: SQLite уже настроен в
`.env.example`.

## Основные API Endpoints

Все endpoints находятся под `/api/v1`.

- `GET /health` - проверка состояния API.
- `POST /sessions` - создание anonymous session.
- `GET /sessions/{session_id}` - получение session.
- `POST /sessions/{session_id}/touch` - обновление `last_seen_at`.
- `POST /parse` - только parsing входных строк.
- `POST /search` - поиск кандидатов в подключенных providers.
- `POST /parse-and-match` - parsing + matching без сохранения.
- `POST /playlists` - parsing + matching + сохранение playlist.
- `GET /playlists?session_id=...` - список playlist для session.
- `GET /playlists/{playlist_id}` - получение playlist.
- `PATCH /playlists/{playlist_id}` - переименование playlist.
- `DELETE /playlists/{playlist_id}` - удаление playlist.
- `PATCH /playlists/{playlist_id}/items/{item_id}` - manual review item.
- `DELETE /playlists/{playlist_id}/items/{item_id}` - удаление item.
- `GET /playlists/{playlist_id}/stats` - метрики playlist.
- `GET /playlists/{playlist_id}/export?format=json|csv|m3u` - export.

Ответы API используют общий формат:

```json
{
  "data": {},
  "meta": { "total": 0, "page": 0 },
  "error": null
}
```

## Research And Evaluation

Оценка parser на размеченном датасете:

```bash
python -m backend.core.parser.evaluation datasets/parser/labeled_tracks.jsonl
```

Сравнение matcher algorithms:

```bash
python -m backend.core.matcher.evaluation --compare-all
```

Сейчас matcher layer содержит:

- `levenshtein` - baseline.
- `jaro_winkler` - более мягкая строковая похожесть.
- `hybrid_levenshtein_jaro_winkler` - default matcher для приложения.

Такой набор удобно использовать в магистерской работе: baseline остается
измеримым, а hybrid matcher можно сравнивать как улучшение для noisy и
transliterated queries.

## Проверка Качества

Backend tests:

```bash
python -m pytest backend
```

Linting и formatting:

```bash
python -m ruff check backend migrations
python -m black --check backend migrations
```

Frontend production build:

```bash
cd frontend
bun run build
```

## Environment

Основные переменные лежат в `.env.example`.

- `PLAYLIST_PARSER_DATABASE_URL` - async SQLAlchemy URL.
- `PLAYLIST_PARSER_AUTO_CREATE_TABLES` - auto-create tables on startup.
- `PLAYLIST_PARSER_CONFIDENCE_THRESHOLD` - threshold для uncertain matches.
- `PLAYLIST_PARSER_ENABLE_DEMO_PROVIDER` - demo catalog для локального запуска.
- `PLAYLIST_PARSER_CORS_ALLOWED_ORIGINS` - разрешенные frontend origins.
- `PLAYLIST_PARSER_SPOTIFY_ACCESS_TOKEN` - optional Spotify token.
- `PLAYLIST_PARSER_YOUTUBE_API_KEY` - optional YouTube API key.

Секреты и локальные файлы не должны попадать в репозиторий: `.env`, SQLite DB,
`node_modules`, `dist`, cache-файлы и локальные agent-файлы игнорируются.

## Документация

Полезные файлы:

- `docs/backend-beginner-guide.md` - подробный beginner guide по backend.
- `docs/backend-testing.md` - ручная проверка backend через Swagger.
- `docs/backend-status.md` - состояние backend и проверенные команды.
- `docs/frontend-start.md` - запуск и возможности frontend.

## Текущий Статус

Backend MVP готов и покрыт тестами. Frontend MVP уже умеет работать с backend:
создавать session, делать preview parse-and-match, создавать playlist, смотреть
items, подтверждать matches, удалять items/playlists, смотреть stats и export.

Следующие крупные направления:

- Улучшить frontend UX и визуальное качество.
- Добавить frontend tests.
- Расширить research datasets.
- Добавить CI pipeline.
- Доработать Spotify OAuth flow вместо ручного access token.
