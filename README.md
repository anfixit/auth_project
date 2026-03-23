# Auth Project

Backend-система аутентификации и авторизации на
**Django REST Framework + PostgreSQL**.

Реализует **кастомную JWT-аутентификацию** и
**RBAC (Role-Based Access Control)** без использования
встроенных auth-пакетов Django.

---

## Стек технологий

- **Python** 3.12
- **Django** 6.0
- **Django REST Framework** 3.17
- **PostgreSQL** 16
- **PyJWT** — генерация и валидация токенов
- **Argon2-cffi** — хеширование паролей (Argon2id)
- **pydantic-settings** — конфигурация через `.env`
- **uv** — управление зависимостями и окружением

---

## Быстрый старт

### Локально

```bash
# 1. Клонировать репозиторий
git clone https://github.com/<you>/auth_project.git
cd auth_project/auth_project

# 2. Создать виртуальное окружение и установить зависимости
uv venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows

uv sync

# 3. Создать .env из примера и заполнить значения
cp .env.example .env

# 4. Применить миграции
uv run python manage.py migrate

# 5. Загрузить тестовые данные
uv run python manage.py loaddata fixtures/initial_data.json

# 6. Запустить сервер
uv run python manage.py runserver
```

### Через Docker

```bash
# 1. Создать .env из примера и заполнить значения
cp .env.example .env

# 2. Запустить
docker compose up --build

# 3. Применить миграции и загрузить фикстуры
docker compose exec web uv run python manage.py migrate
docker compose exec web uv run python manage.py loaddata \
    fixtures/initial_data.json
```

### Создать администратора

```bash
uv run python manage.py shell
```

```python
from apps.users.services import create_user
from apps.access.models import Role, UserRole

user = create_user(
    email='admin@example.com',
    password='AdminPass1!',
    first_name='Admin',
    last_name='User',
)
role = Role.objects.get(name='admin')
UserRole.objects.create(user=user, role=role)
```

---

## Структура проекта

```
auth_project/
├── apps/
│   ├── access/          ← RBAC: роли, права, бизнес-объекты
│   ├── auth_core/       ← JWT: токены, middleware, декораторы
│   ├── mock_views/      ← mock бизнес-объектов для демонстрации
│   ├── users/           ← регистрация, профиль, soft delete
│   ├── logger.py        ← настройка логирования
│   └── utils.py         ← общие утилиты
├── config/              ← настройки Django
├── fixtures/            ← начальные данные
├── logs/                ← лог-файлы (не в git)
├── tests/               ← тесты
├── .env.example
├── .python-version
├── .pre-commit-config.yaml
├── constants.py         ← кросс-доменные константы проекта
├── docker-compose.yml
├── Dockerfile
├── manage.py
└── pyproject.toml
```

---

## Схема базы данных

```
┌─────────────┐       ┌────────────┐       ┌──────────────┐
│    users    │       │ user_roles │       │    roles     │
│─────────────│       │────────────│       │──────────────│
│ id          │◄──────│ user_id    │──────►│ id           │
│ email       │       │ role_id    │       │ name         │
│ first_name  │       │ assigned_at│       │ description  │
│ last_name   │       └────────────┘       └──────────────┘
│ patronymic  │                                    │
│ password    │                                    │
│ is_active   │                           ┌────────▼───────────┐
│ is_staff    │                           │    access_rules    │
│ created_at  │                           │────────────────────│
│ updated_at  │                           │ id                 │
└─────────────┘                           │ role_id            │
       │                                  │ element_id         │
       │                                  │ read               │
┌──────▼──────────┐                       │ read_all           │
│ refresh_tokens  │   ┌───────────────────│ create             │
│─────────────────│   │                   │ update             │
│ id              │   │                   │ update_all         │
│ user_id         │   │                   │ delete             │
│ token           │   │                   │ delete_all         │
│ created_at      │   │                   └────────────────────┘
│ expires_at      │   │
└─────────────────┘   │  ┌──────────────────────┐
                      └─►│  business_elements   │
                         │──────────────────────│
                         │ id                   │
                         │ name                 │
                         │ description          │
                         └──────────────────────┘
```

---

## Система разграничения доступа (RBAC)

Каждый пользователь может иметь одну или несколько ролей.
Каждая роль определяет матрицу прав доступа к бизнес-объектам.

### Роли

| Роль    | Описание                                       |
|---------|------------------------------------------------|
| admin   | Полный доступ ко всем ресурсам и операциям    |
| manager | Управление товарами, магазинами и заказами    |
| user    | Доступ только к собственным данным            |
| guest   | Просмотр каталога (products, shops)           |

### Матрица прав

| Роль    | Объект   | read | read_all | create | update | update_all | delete | delete_all |
|---------|----------|:----:|:--------:|:------:|:------:|:----------:|:------:|:----------:|
| admin   | все      |  ✔   |    ✔     |   ✔    |   ✔    |     ✔      |   ✔    |     ✔      |
| manager | products |  ✔   |    ✔     |   ✔    |   ✔    |     ✔      |   ✔    |     ✖      |
| manager | orders   |  ✔   |    ✔     |   ✔    |   ✔    |     ✔      |   ✖    |     ✖      |
| user    | products |  ✔   |    ✖     |   ✔    |   ✔    |     ✖      |   ✔    |     ✖      |
| user    | orders   |  ✔   |    ✖     |   ✔    |   ✔    |     ✖      |   ✖    |     ✖      |
| guest   | products |  ✔   |    ✔     |   ✖    |   ✖    |     ✖      |   ✖    |     ✖      |
| guest   | shops    |  ✔   |    ✔     |   ✖    |   ✖    |     ✖      |   ✖    |     ✖      |

### Поток проверки прав

```
Запрос → JWTAuthMiddleware (извлекает user_id, roles из токена)
       → @has_permission(element, action)
       → check_permission() → кеш → AccessRule в БД
       → 200 OK / 401 / 403
```

---

## Поток аутентификации

**POST /api/v1/auth/login/**
- Проверка email + Argon2id-хеш пароля
- Генерация `access_token` (15 мин) и `refresh_token` (7 дней)
- `refresh_token` сохраняется в таблице `refresh_tokens`

**Дальнейшие запросы:**
```
Authorization: Bearer <access_token>
```

**POST /api/v1/auth/logout/**
- Удаляет все `refresh_tokens` пользователя из БД
- `access_token` истекает автоматически

**POST /api/v1/auth/refresh/**
- Проверяет `refresh_token` в БД
- Выдаёт новый `access_token`

---

## API Reference

### Auth

| Метод | URL                      | Доступ       | Описание           |
|-------|--------------------------|--------------|--------------------|
| POST  | `/api/v1/auth/login/`    | Публичный    | Получить токены    |
| POST  | `/api/v1/auth/logout/`   | Авторизован  | Отозвать токены    |
| POST  | `/api/v1/auth/refresh/`  | Публичный    | Обновить токен     |

### Users

| Метод  | URL                        | Доступ      | Описание             |
|--------|----------------------------|-------------|----------------------|
| POST   | `/api/v1/users/register/`  | Публичный   | Регистрация          |
| GET    | `/api/v1/users/me/`        | Авторизован | Профиль              |
| PATCH  | `/api/v1/users/me/update/` | Авторизован | Обновить профиль     |
| DELETE | `/api/v1/users/me/delete/` | Авторизован | Мягкое удаление      |

### Access (только admin)

| Метод  | URL                                    | Описание              |
|--------|----------------------------------------|-----------------------|
| GET    | `/api/v1/access/roles/`                | Список ролей          |
| POST   | `/api/v1/access/roles/create/`         | Создать роль          |
| DELETE | `/api/v1/access/roles/<id>/delete/`    | Удалить роль          |
| GET    | `/api/v1/access/elements/`             | Список объектов       |
| GET    | `/api/v1/access/rules/`                | Матрица прав          |
| POST   | `/api/v1/access/rules/create/`         | Создать правило       |
| PATCH  | `/api/v1/access/rules/<id>/update/`    | Изменить правило      |
| DELETE | `/api/v1/access/rules/<id>/delete/`    | Удалить правило       |
| GET    | `/api/v1/access/user-roles/`           | Назначения ролей      |
| POST   | `/api/v1/access/user-roles/assign/`    | Назначить роль        |
| DELETE | `/api/v1/access/user-roles/<id>/remove/` | Снять роль          |

### Mock

| Метод | URL                           | Права             | Описание      |
|-------|-------------------------------|-------------------|---------------|
| GET   | `/api/v1/mock/products/`      | products.read_all | Все товары    |
| GET   | `/api/v1/mock/products/<id>/` | products.read     | Один товар    |
| GET   | `/api/v1/mock/orders/`        | orders.read_all   | Все заказы    |
| GET   | `/api/v1/mock/shops/`         | shops.read_all    | Все магазины  |

---

## Тестирование

```bash
uv run pytest
```

---

## Безопасность

- Пароли хешируются через **Argon2id** (`time_cost=2`, `memory_cost=64MB`)
- JWT содержит только `user_id` и `roles` — без чувствительных данных
- Refresh-токены хранятся в БД и инвалидируются при logout
- Защита от timing-атак при аутентификации
- Soft delete — данные сохраняются, логин невозможен
- Mass-assignment protection при обновлении профиля
- Кеширование матрицы прав с инвалидацией при изменениях
