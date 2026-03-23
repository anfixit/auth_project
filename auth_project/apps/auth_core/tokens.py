"""Утилиты генерации и валидации JWT-токенов."""

__all__ = [
    'decode_token',
    'generate_access_token',
    'generate_refresh_token',
]

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from django.conf import settings

from apps.auth_core.constants import JWT_ALGORITHM


def _secret() -> str:
    """Получить секретный ключ из настроек Django.

    Returns:
        Строка с секретным ключом.
    """
    return settings.SECRET_KEY


def generate_access_token(
    user_id: int,
    role_names: list[str],
) -> str:
    """Создать короткоживущий access-токен.

    Payload содержит только id и роли —
    без чувствительных данных.

    Args:
        user_id: Идентификатор пользователя.
        role_names: Список названий ролей пользователя.

    Returns:
        Подписанный JWT access-токен.
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        'sub': str(user_id),
        'roles': role_names,
        'type': 'access',
        'iat': now,
        'exp': now
        + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        ),
    }
    return jwt.encode(payload, _secret(), algorithm=JWT_ALGORITHM)


def generate_refresh_token(user_id: int) -> str:
    """Создать долгоживущий refresh-токен.

    Хранится в БД — можно инвалидировать при logout.

    Args:
        user_id: Идентификатор пользователя.

    Returns:
        Подписанный JWT refresh-токен.
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        'sub': str(user_id),
        'type': 'refresh',
        'iat': now,
        'exp': now
        + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
        ),
    }
    return jwt.encode(payload, _secret(), algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Декодировать и верифицировать токен.

    Args:
        token: Строка JWT-токена.

    Returns:
        Словарь с payload токена.

    Raises:
        jwt.ExpiredSignatureError: Токен истёк.
        jwt.InvalidTokenError: Токен невалиден.
    """
    return jwt.decode(
        token,
        _secret(),
        algorithms=[JWT_ALGORITHM],
    )
