# FastAPI Task Manager

[Проверенный запуск и ограничения](VERIFICATION.md).

REST API: регистрация, JWT-вход и управление своими задачами.
Чужие задачи недоступны. Поддерживаются приоритет, статус, фильтры и пагинация.

```bash
python -m venv .venv
# Активируйте .venv согласно вашей ОС.
python -m pip install . -r requirements-dev.txt
# Скопируйте .env.example в .env и задайте локальные DATABASE_URL и SECRET_KEY.
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Для Windows команды после активации такие же. PostgreSQL URL должен использовать
драйвер `postgresql+asyncpg`. Swagger: `/docs`, health: `/health`.

Маршруты: POST `/auth/register`, POST `/auth/login` (форма username/password),
GET `/auth/me`; GET/POST `/tasks/`, GET/PUT/DELETE `/tasks/{id}`.
Токен передаётся через `Authorization: Bearer …`.

```bash
python -m pytest
docker compose up --build
```

Тесты используют отдельную SQLite-БД. Не задавайте в тестовом окружении рабочую БД.
Роли администратора и интеграции с платежами не реализованы.
