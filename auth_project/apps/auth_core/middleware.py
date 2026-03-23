"""Middleware приложения auth_core."""

__all__ = ["JWTAuthMiddleware"]

from collections.abc import Callable

import jwt
from django.http import HttpRequest, HttpResponse

from apps.auth_core.tokens import decode_token
from apps.logger import get_logger

logger = get_logger(__name__)


class JWTAuthMiddleware:
    """Идентифицирует пользователя из заголовка Authorization.

    Ожидаемый формат заголовка:
        Authorization: Bearer <access_token>

    Устанавливает до обработки view:
        request.user_id  — int | None
        request.roles    — list[str]

    Не блокирует запрос — 401/403 возвращают
    декораторы login_required и has_permission.
    """

    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse],
    ) -> None:
        """Инициализировать middleware.

        Args:
            get_response: Следующий обработчик в цепочке.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Обработать запрос: извлечь и проверить токен.

        Args:
            request: Входящий HTTP-запрос.

        Returns:
            HTTP-ответ от следующего обработчика.
        """
        request.user_id = None  # type: ignore[attr-defined]
        request.roles = []  # type: ignore[attr-defined]

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer ") :]
            try:
                payload = decode_token(token)
                if payload.get("type") == "access":
                    request.user_id = int(payload["sub"])  # type: ignore[attr-defined]
                    request.roles = payload.get("roles", [])  # type: ignore[attr-defined]
            except jwt.ExpiredSignatureError:
                logger.warning("JWT токен истёк")
            except jwt.InvalidTokenError:
                logger.warning("Невалидный JWT токен")

        return self.get_response(request)
