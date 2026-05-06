# Frontend Start

Первый frontend уже подключен к готовому backend API.

## Что Уже Есть

- React + TypeScript + Vite.
- Session создается автоматически и хранится в `localStorage`.
- Можно создать playlist из списка строк.
- Можно выбрать сохраненный playlist.
- Можно переименовать или удалить playlist.
- Можно подтвердить item вручную.
- Можно удалить item.
- Можно посмотреть stats.
- Можно получить export в JSON, CSV или M3U.

## Как Запустить

В первом PowerShell запусти backend из корня проекта:

```powershell
python -m uvicorn backend.main:app --reload
```

Во втором PowerShell запусти frontend:

```powershell
cd frontend
bun install
bun run dev
```

Открой:

```text
http://127.0.0.1:5173
```

## Если Backend На Другом Адресе

Создай файл `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

После изменения `.env` перезапусти frontend dev server.

## Проверка

Production build:

```powershell
bun run build
```

Ожидается, что TypeScript и Vite build проходят без ошибок.
