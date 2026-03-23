Я не могу буквально отправить файл как вложение, но вот содержимое, которое можно сразу сохранить в `README.md` (это ровно один файл, без лишнего текста вокруг). [redocly](https://redocly.com/docs/realm/access/page-permissions)

```markdown
# Auth Project

Backend-система аутентификации и авторизации на **Django REST Framework + PostgreSQL**.  
Проект реализует **кастомную JWT-аутентификацию** и **RBAC (Role-Based Access Control)** без использования встроенных auth-пакетов Django.[web:2]

---

## Стек технологий

- **Python:** 3.12  
- **Django:** 5.1  
- **Django REST Framework:** 3.15  
- **PostgreSQL:** 16  
- **PyJWT:** генерация и валидация токенов  
- **Argon2-cffi:** безопасное хеширование паролей (Argon2id)  
- **uv:** управление зависимостями и окружением[web:1]

---

## Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone https://github.com/<you>/auth_project.git
cd auth_project

# 2. Создать .env из примера и заполнить значения
cp .env.example .env

# 3. Запустить через Docker
docker compose up --build

# 4. Применить миграции и загрузить фикстуры
docker compose exec web uv run python manage.py migrate
docker compose exec web uv run python manage.py loaddata fixtures/initial_data.json

# 5. Создать admin-пользователя в Django shell
docker compose exec web uv run python manage.py shell
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
│ refresh_tokens  │     ┌─────────────────│ create             │
│─────────────────│     │                 │ update             │
│ id              │     │                 │ update_all         │
│ user_id         │     │                 │ delete             │
│ token           │     │                 │ delete_all         │
│ created_at      │     │                 └────────────────────┘
│ expires_at      │     │
└─────────────────┘     │  ┌──────────────────────┐
                        └─►│  business_elements   │
                           │──────────────────────│
                           │ id                   │
                           │ name                 │
                           │ description          │
                           └──────────────────────┘
```

---

## Система разграничения доступа (RBAC)

### Концепция
Каждый пользователь может иметь одну или несколько ролей.  
Каждая роль определяет **матрицу прав доступа** к бизнес-объектам.[web:2]

Процесс проверки прав:
1. Middleware извлекает `user_id` и `roles` из JWT.  
2. Декоратор `@has_permission(element, action)` вызывает `check_permission()`.  
3. Если хотя бы одна роль имеет требуемое право — доступ предоставляется.  
4. Иначе возвращается **403 Forbidden**.[web:5]

---

### Роли

| Роль   | Описание                                      |
|--------|-----------------------------------------------|
| admin  | Полный доступ ко всем ресурсам и операциям   |
| manager| Управление товарами, магазинами и заказами   |
| user   | Доступ только к собственным данным (owner_id)|
| guest  | Просмотр каталога (products, shops)          |


---

### Матрица прав

| Роль    | Объект   | read | read_all | create | update | update_all | delete | delete_all |
|--------|----------|:----:|:--------:|:------:|:------:|:----------:|:------:|:----------:|
| admin  | все      |  ✔   |    ✔     |   ✔    |   ✔    |     ✔      |   ✔    |     ✔      |
| manager| products |  ✔   |    ✔     |   ✔    |   ✔    |     ✔      |   ✔    |     ✖      |
| manager| orders   |  ✔   |    ✔     |   ✔    |   ✔    |     ✔      |   ✖    |     ✖      |
| user   | products |  ✔   |    ✖     |   ✔    |   ✔    |     ✖      |   ✔    |     ✖      |
| user   | orders   |  ✔   |    ✖     |   ✔    |   ✔    |     ✖      |   ✖    |     ✖      |
| guest  | products |  ✔   |    ✔     |   ✖    |   ✖    |     ✖      |   ✖    |     ✖      |
| guest  | shops    |  ✔   |    ✔     |   ✖    |   ✖    |     ✖      |   ✖    |     ✖      |


---

## Поток аутентификации

**POST /api/v1/auth/login/**  
- Проверка email + Argon2-хеш пароля  
- Генерация `access_token` (15 мин)  
- Генерация `refresh_token` (7 дней)  
- `refresh_token` сохраняется в таблице `refresh_tokens`[web:10]

**Дальнейшие запросы:**
```
Authorization: Bearer <access_token>
```
Middleware:
1. Декодирует JWT  
2. Устанавливает `request.user_id` и `request.roles`  
3. `@has_permission` проверяет доступы[web:6]

**POST /api/v1/auth/logout/**  
- Удаляет все refresh_tokens пользователя из БД  
- Access-token истекает автоматически  

**POST /api/v1/auth/refresh/**  
- Проверяет `refresh_token` в БД  
- Выдаёт новый access_token[web:5]

---

## API Reference

### Auth

| Метод | URL | Доступ | Описание |
|--------|-----|--------|-----------|
| POST | `/api/v1/auth/login/` | Публичный | Получить токены |
| POST | `/api/v1/auth/logout/` | Авторизован | Отозвать токены |
| POST | `/api/v1/auth/refresh/` | Публичный | Обновить access token |

### Users

| Метод | URL | Доступ | Описание |
|--------|-----|--------|-----------|
| POST | `/api/v1/users/register/` | Публичный | Регистрация |
| GET | `/api/v1/users/me/` | Авторизован | Профиль |
| PATCH | `/api/v1/users/me/update/` | Авторизован | Обновить профиль |
| DELETE | `/api/v1/users/me/delete/` | Авторизован | Мягкое удаление |

### Access (только admin)

| Метод | URL | Права | Описание |
|--------|-----|--------|-----------|
| GET | `/api/v1/access/roles/` | access_rules.read_all | Список ролей |
| POST | `/api/v1/access/roles/create/` | access_rules.create | Создать роль |
| DELETE | `/api/v1/access/roles/<id>/delete/` | access_rules.delete_all | Удалить роль |
| GET | `/api/v1/access/elements/` | access_rules.read_all | Список объектов |
| GET | `/api/v1/access/rules/` | access_rules.read_all | Матрица прав |
| POST | `/api/v1/access/rules/create/` | access_rules.create | Создать правило |
| PATCH | `/api/v1/access/rules/<id>/update/` | access_rules.update_all | Изменить правило |
| DELETE | `/api/v1/access/rules/<id>/delete/` | access_rules.delete_all | Удалить правило |
| GET | `/api/v1/access/user-roles/` | users.read_all | Назначения ролей |
| POST | `/api/v1/access/user-roles/assign/` | access_rules.create | Назначить роль |
| DELETE | `/api/v1/access/user-roles/<id>/remove/` | access_rules.delete_all | Снять роль |

### Mock

| Метод | URL | Права | Описание |
|--------|-----|--------|-----------|
| GET | `/api/v1/mock/products/` | products.read_all | Все товары |
| GET | `/api/v1/mock/products/<id>/` | products.read | Один товар |
| GET | `/api/v1/mock/orders/` | orders.read_all | Все заказы |
| GET | `/api/v1/mock/shops/` | shops.read_all | Все магазины |

---

## Тестирование

```bash
uv run pytest
```

---

## Безопасность

- Пароли хешируются через **Argon2id** (`time_cost=2`, `memory_cost=64MB`)  
- JWT включает только `user_id` и `roles`  
- Refresh-токены хранятся в БД и инвалидируются при logout  
- Реализована защита от timing-атак при аутентификации  
- Soft delete — данные сохраняются, но логин невозможен  
- Mass-assignment protection при обновлении профиля[web:7]

---
