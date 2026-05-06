# Чеклист Ручного Тестирования Backend

Этот сценарий нужен, чтобы проверить готовый backend перед переходом к frontend
или перед демонстрацией проекта.

## 1. Подготовка

Установить зависимости:

```bash
python -m pip install -e ".[dev]"
```

Создать `.env`:

```bash
cp .env.example .env
```

Применить миграции:

```bash
alembic upgrade head
```

Запустить backend:

```bash
python -m uvicorn backend.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## 2. Быстрый Smoke Test

PowerShell:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health"
```

Ожидается:

```json
{
  "data": { "status": "ok", "version": "0.1.0" },
  "meta": null,
  "error": null
}
```

## 3. Создать Session

```powershell
$session = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/sessions" `
  -ContentType "application/json" `
  -Body '{"display_name":"Manual Test"}'

$sessionId = $session.data.session_id
$sessionId
```

Проверить session:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/sessions/$sessionId"
```

Обновить активность:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/sessions/$sessionId/touch"
```

## 4. Parse

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/parse" `
  -ContentType "application/json" `
  -Body '{"raw_lines":["Daft Punk - Around the World","Кино - Группа крови"]}'
```

Проверить, что в `data.items` есть artist/title/confidence/pattern.

## 5. Search

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/search" `
  -ContentType "application/json" `
  -Body '{"query":"Daft Punk Around the World","limit":3}'
```

Проверить, что возвращаются demo candidates.

## 6. Parse And Match

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/parse-and-match" `
  -ContentType "application/json" `
  -Body '{"raw_lines":["Daft Punk - Around the World","Radiohead - Nude"],"match_limit":3}'
```

Проверить `best_score`, `is_uncertain`, `source_reports` и explanation.

## 7. Создать Playlist

```powershell
$playlistResponse = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/playlists" `
  -ContentType "application/json" `
  -Body "{`"session_id`":`"$sessionId`",`"name`":`"Manual Playlist`",`"raw_lines`":[`"Daft Punk - Around the World`",`"Radiohead - Nude`"],`"match_limit`":3}"

$playlistId = $playlistResponse.data.playlist_id
$itemId = $playlistResponse.data.items[0].item_id
$playlistId
$itemId
```

## 8. Получить И Изменить Playlist

Получить плейлист:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/playlists/$playlistId"
```

Переименовать:

```powershell
Invoke-RestMethod `
  -Method Patch `
  -Uri "http://127.0.0.1:8000/api/v1/playlists/$playlistId" `
  -ContentType "application/json" `
  -Body '{"name":"Renamed Manual Playlist"}'
```

Получить список плейлистов session:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/playlists?session_id=$sessionId"
```

## 9. Manual Review Item

```powershell
Invoke-RestMethod `
  -Method Patch `
  -Uri "http://127.0.0.1:8000/api/v1/playlists/$playlistId/items/$itemId" `
  -ContentType "application/json" `
  -Body '{"match_track_id":"manual:confirmed-track","match_score":0.99,"match_algorithm":"manual","source":"manual","is_uncertain":false}'
```

Проверить, что `is_uncertain=false`, а match fields обновились.

## 10. Stats

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/playlists/$playlistId/stats"
```

Проверить:

- `total_items`
- `uncertain_count`
- `confirmed_count`
- `average_match_score`
- `source_counts`
- `algorithm_counts`

## 11. Export

JSON:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/playlists/$playlistId/export?format=json"
```

CSV:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/playlists/$playlistId/export?format=csv"
```

M3U:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/playlists/$playlistId/export?format=m3u"
```

## 12. Delete

Удалить item:

```powershell
Invoke-RestMethod -Method Delete -Uri "http://127.0.0.1:8000/api/v1/playlists/$playlistId/items/$itemId"
```

Удалить playlist:

```powershell
Invoke-RestMethod -Method Delete -Uri "http://127.0.0.1:8000/api/v1/playlists/$playlistId"
```

После удаления запрос должен вернуть `PLAYLIST_NOT_FOUND`:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/playlists/$playlistId"
```

## 13. Research Checks

```bash
evaluate-parser datasets/parser/labeled_tracks.jsonl
evaluate-matcher --compare-all
```

## 14. Автоматические Проверки

```bash
python -m pytest backend
python -m ruff check backend migrations
python -m black --check backend migrations
```

Все команды должны проходить без ошибок.
