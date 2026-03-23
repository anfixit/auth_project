from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from django.conf import settings

ALGORITHM = "HS256"


def _secret() -> str:
    return settings.SECRET_KEY


def generate_access_token(
    user_id: int,
    role_names: list[str],
) -> str:
    """
    Создать короткоживущий access token.
    Payload содержит только id и роли —
    без чувствительных данных.
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "roles": role_names,
        "type": "access",
        "iat": now,
        "exp": now
        + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def generate_refresh_token(user_id: int) -> str:
    """
    Создать долгоживущий refresh token.
    Хранится в БД — можно инвалидировать при logout.
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Декодировать и верифицировать токен.

    Raises:
        jwt.ExpiredSignatureError: токен истёк.
        jwt.InvalidTokenError: токен невалиден.
    """
    return jwt.decode(
        token,
        _secret(),
        algorithms=[ALGORITHM],
    )
