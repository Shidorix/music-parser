# Как Проверить Backend С Нуля

Этот файл для ситуации: “я открыл проект и пока не понимаю, что где работает”.
Идем спокойно, по шагам. После этого ты сможешь сам пощупать backend и понять
основной сценарий приложения.

## 1. Что Вообще Есть В Проекте

Проект называется Playlist Parser Web Application.

Его смысл:

1. Пользователь вставляет список треков обычным текстом.
2. Backend разбирает строки: где artist, где title.
3. Потом backend ищет похожие треки через matcher.
4. Результат можно сохранить как playlist.
5. Потом можно вручную исправить uncertain matches.
6. Потом можно посмотреть статистику и экспортировать playlist.

Сейчас мы тестируем только backend, то есть серверную часть. Frontend пока еще
не делали.

## 2. Какая Сейчас База Данных

По умолчанию у тебя используется SQLite.

Настройка лежит в `.env.example`:

```env
PLAYLIST_PARSER_DATABASE_URL=sqlite+aiosqlite:///./playlist_parser.db
```

Это значит:

- база будет обычным файлом `playlist_parser.db` в корне проекта;
- отдельный сервер базы данных запускать не нужно;
- для локального тестирования этого достаточно.

Docker Compose с PostgreSQL уже подготовлен, но сейчас его можно не трогать.
Пока работаем через SQLite.

## 3. Что Нужно Установить

Открой PowerShell в корне проекта:

```powershell
cd G:\IT-Projects\<project-folder>
```

Установи зависимости:

```powershell
python -m pip install -e ".[dev]"
```

Если зависимости уже стоят, команда просто быстро завершится или обновит пакет.

## 4. Создать `.env`

В корне проекта есть файл `.env.example`. Это пример настроек.

Скопируй его в `.env`:

```powershell
Copy-Item .env.example .env
```

Если файл `.env` уже есть, PowerShell может спросить про замену. Пока можно
оставить старый файл, если ты его уже создавал.

Минимально важные настройки:

```env
PLAYLIST_PARSER_DATABASE_URL=sqlite+aiosqlite:///./playlist_parser.db
PLAYLIST_PARSER_AUTO_CREATE_TABLES=false
PLAYLIST_PARSER_ENABLE_DEMO_PROVIDER=true
```

Spotify и YouTube ключи пока можно не указывать. Demo provider уже дает тестовые
треки для проверки.

## 5. Создать Таблицы В SQLite

У нас есть миграции Alembic. Они создают таблицы в базе данных.

Запусти:

```powershell
python -m alembic upgrade head
```

После этого в корне проекта должен появиться файл:

```text
playlist_parser.db
```

Это и есть твоя локальная SQLite база.

Если файл не появился, проверь, что команда завершилась без ошибки. Сейчас основной
способ создания таблиц — именно Alembic миграции.

## 6. Запустить Backend

Запусти сервер:

```powershell
python -m uvicorn backend.main:app --reload
```

Если все хорошо, увидишь что-то похожее:

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete.
```

Важно: это окно PowerShell теперь занято сервером. Не закрывай его, пока тестируешь.

Если нужно остановить backend:

```text
Ctrl + C
```

## 7. Открыть Swagger

Открой в браузере:

```text
http://127.0.0.1:8000/docs
```

Swagger UI — это страница, где можно нажимать endpoint'ы backend без frontend.

Там ты увидишь группы:

- `health`
- `sessions`
- `parse`
- `search`
- `parse-and-match`
- `playlists`

## 8. Самая Простая Проверка: Health

В Swagger найди:

```text
GET /api/v1/health
```

Нажми:

```text
Try it out
Execute
```

Ожидаемый ответ:

```json
{
  "data": {
    "status": "ok",
    "version": "0.1.0"
  },
  "meta": null,
  "error": null
}
```

Если это работает, backend живой.

## 9. Создать Session

Session нужна, чтобы потом привязать playlist к пользователю. Пока это anonymous
session без логина и пароля.

В Swagger найди:

```text
POST /api/v1/sessions
```

Нажми `Try it out` и вставь body:

```json
{
  "display_name": "Manual Test"
}
```

Нажми `Execute`.

В ответе будет примерно:

```json
{
  "data": {
    "session_id": "....",
    "display_name": "Manual Test",
    "created_at": "...",
    "last_seen_at": "...",
    "explanation": "Created anonymous user session."
  },
  "meta": {
    "total": 1,
    "page": 0
  },
  "error": null
}
```

Скопируй `session_id`. Он понадобится дальше.

## 10. Проверить Parser

Parser разбирает строки на artist/title.

В Swagger найди:

```text
POST /api/v1/parse
```

Body:

```json
{
  "raw_lines": [
    "Daft Punk - Around the World",
    "Radiohead - Nude",
    "Кино - Группа крови"
  ]
}
```

Ожидаешь увидеть в ответе `items`, где у каждого трека есть:

- `raw_input`
- `artist`
- `title`
- `confidence`
- `pattern`
- `language`

Примерно так:

```json
{
  "raw_input": "Daft Punk - Around the World",
  "artist": "Daft Punk",
  "title": "Around the World",
  "confidence": 0.95,
  "pattern": "artist_title"
}
```

## 11. Проверить Search

Search ищет кандидатов треков.

Пока без Spotify/YouTube ключей работает demo catalog.

В Swagger найди:

```text
POST /api/v1/search
```

Body:

```json
{
  "query": "Daft Punk Around the World",
  "limit": 3
}
```

В ответе должны быть кандидаты, например:

```text
demo:daft-punk-around-the-world
```

Это значит, что demo search работает.

## 12. Проверить Parse And Match

Это главный алгоритмический сценарий без сохранения в БД.

В Swagger найди:

```text
POST /api/v1/parse-and-match
```

Body:

```json
{
  "raw_lines": [
    "Daft Punk - Around the World",
    "Radiohead - Nude",
    "Bonobo - Kerala"
  ],
  "match_limit": 3
}
```

Смотри в ответе:

- `parsed_track`: как строка распарсилась;
- `match_result`: какие кандидаты найдены;
- `best_score`: лучший score;
- `is_uncertain`: надо ли вручную проверить;
- `source_reports`: какие источники использовались;
- `explanation`: почему результат считается уверенным или uncertain.

Это важный endpoint для магистерской, потому что он показывает explainability.

## 13. Создать Playlist

Теперь сохраняем результат в SQLite.

В Swagger найди:

```text
POST /api/v1/playlists
```

Body, но замени `PASTE_SESSION_ID_HERE` на свой `session_id`:

```json
{
  "session_id": "PASTE_SESSION_ID_HERE",
  "name": "My Manual Test Playlist",
  "raw_lines": [
    "Daft Punk - Around the World",
    "Radiohead - Nude",
    "Bonobo - Kerala"
  ],
  "match_limit": 3
}
```

В ответе будет:

- `playlist_id`
- `items`
- `total_items`
- `uncertain_count`

Скопируй:

- `playlist_id`
- `item_id` любого item

Они понадобятся дальше.

## 14. Получить Playlist По ID

В Swagger найди:

```text
GET /api/v1/playlists/{playlist_id}
```

Вставь свой `playlist_id`.

Проверь, что backend возвращает сохраненный playlist и его items.

Если это работает, значит SQLite persistence работает.

## 15. Получить Playlists По Session

В Swagger найди:

```text
GET /api/v1/playlists
```

В query parameter `session_id` вставь свой `session_id`.

Backend должен вернуть список playlist'ов этой session.

## 16. Переименовать Playlist

В Swagger найди:

```text
PATCH /api/v1/playlists/{playlist_id}
```

Body:

```json
{
  "name": "Renamed Playlist"
}
```

После выполнения снова сделай:

```text
GET /api/v1/playlists/{playlist_id}
```

Название должно измениться.

## 17. Ручная Проверка Item

Это имитация ситуации, когда пользователь руками исправляет match.

В Swagger найди:

```text
PATCH /api/v1/playlists/{playlist_id}/items/{item_id}
```

Body:

```json
{
  "match_track_id": "manual:confirmed-track",
  "match_score": 0.99,
  "match_algorithm": "manual",
  "source": "manual",
  "is_uncertain": false
}
```

После этого item должен получить:

- `match_track_id = manual:confirmed-track`
- `match_algorithm = manual`
- `source = manual`
- `is_uncertain = false`

Это будущий сценарий для frontend: пользователь подтверждает или исправляет
сомнительный результат.

## 18. Посмотреть Stats

В Swagger найди:

```text
GET /api/v1/playlists/{playlist_id}/stats
```

Там будут метрики:

- `total_items`
- `uncertain_count`
- `confirmed_count`
- `average_match_score`
- `average_parser_confidence`
- `source_counts`
- `algorithm_counts`
- `uncertain_positions`

Это полезно и для UI, и для магистерской.

## 19. Export Playlist

В Swagger найди:

```text
GET /api/v1/playlists/{playlist_id}/export
```

Параметр `format` может быть:

```text
json
csv
m3u
```

Проверь по очереди:

```text
format=json
format=csv
format=m3u
```

В ответе будет:

- `filename`
- `format`
- `media_type`
- `content`

То есть backend умеет подготовить содержимое файла для экспорта.

## 20. Удалить Item

В Swagger найди:

```text
DELETE /api/v1/playlists/{playlist_id}/items/{item_id}
```

После удаления backend вернет обновленный playlist.

Проверь, что `total_items` уменьшился.

## 21. Удалить Playlist

В Swagger найди:

```text
DELETE /api/v1/playlists/{playlist_id}
```

После удаления попробуй снова:

```text
GET /api/v1/playlists/{playlist_id}
```

Ожидаемый результат:

```json
{
  "data": null,
  "meta": null,
  "error": {
    "code": "PLAYLIST_NOT_FOUND",
    "message": "Playlist was not found."
  }
}
```

Если так и произошло, delete работает.

## 22. Как Посмотреть, Что Данные Реально В SQLite

Файл базы:

```text
playlist_parser.db
```

Его можно открыть любым SQLite viewer, например:

- DB Browser for SQLite
- SQLite extension в IDE
- любой другой SQLite client

Таблицы:

- `user_sessions`
- `playlists`
- `playlist_items`
- `alembic_version`

Если ты создавал session и playlist, данные будут там.

## 23. Автоматические Проверки

Когда хочешь убедиться, что backend не сломан:

```powershell
python -m pytest backend
```

Ожидаемо сейчас:

```text
96 passed
```

Проверка стиля:

```powershell
python -m ruff check backend migrations
python -m black --check backend migrations
```

Ожидаемо:

```text
All checks passed
```

## 24. Исследовательские Команды

Parser evaluation:

```powershell
python -m backend.core.parser.evaluation datasets\parser\labeled_tracks.jsonl
```

Matcher comparison:

```powershell
python -m backend.core.matcher.evaluation --compare-all
```

Эти команды нужны для магистерской: они показывают измеримые метрики качества.

## 25. Типичные Проблемы

### Не открывается Swagger

Проверь, что backend запущен:

```powershell
python -m uvicorn backend.main:app --reload
```

И открывай:

```text
http://127.0.0.1:8000/docs
```

### Ошибка `address already in use`

Значит порт `8000` уже занят. Можно запустить на другом порту:

```powershell
python -m uvicorn backend.main:app --reload --port 8001
```

Тогда Swagger:

```text
http://127.0.0.1:8001/docs
```

### Нет файла `playlist_parser.db`

Запусти миграции:

```powershell
python -m alembic upgrade head
```

В обычном локальном запуске держи:

```env
PLAYLIST_PARSER_AUTO_CREATE_TABLES=false
```

Так Alembic будет единственным источником схемы БД.

### Ошибка `table playlists already exists`

Это значит, что таблицы уже были созданы раньше, но Alembic не записал это в свою
таблицу версий. Обычно так происходит, если backend был запущен с:

```env
PLAYLIST_PARSER_AUTO_CREATE_TABLES=true
```

Самый простой вариант для тестовой локальной SQLite-базы — удалить старый файл БД
и создать его заново миграциями:

```powershell
Remove-Item .\playlist_parser.db
python -m alembic upgrade head
```

Важно: это удалит локальные тестовые sessions/playlists. Если там есть данные,
которые нужно сохранить, не удаляй файл. Тогда можно просто пометить текущую схему
как актуальную для Alembic:

```powershell
python -m alembic stamp head
```

Для учебного тестирования обычно проще удалить `playlist_parser.db` и начать с
чистой базы.

### Spotify/YouTube не работают

Это нормально, если ты не указал ключи.

Без ключей работает demo provider:

```env
PLAYLIST_PARSER_ENABLE_DEMO_PROVIDER=true
```

Для тестирования MVP этого достаточно.

## 26. Главный Сценарий, Который Нужно Понять

Минимальный путь:

1. `GET /health` — backend живой.
2. `POST /sessions` — создали session.
3. `POST /parse` — поняли, как строки разбираются.
4. `POST /parse-and-match` — поняли, как строки матчятся с треками.
5. `POST /playlists` — сохранили playlist в SQLite.
6. `GET /playlists/{id}` — прочитали playlist из SQLite.
7. `PATCH /playlists/{id}/items/{item_id}` — вручную подтвердили match.
8. `GET /playlists/{id}/stats` — посмотрели метрики.
9. `GET /playlists/{id}/export` — экспортировали результат.

Если ты прошел эти шаги, ты понял backend достаточно, чтобы переходить к frontend.
