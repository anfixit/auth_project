from collections.abc import Callable

import jwt
from django.http import HttpRequest, HttpResponse

from apps.auth_core.tokens import decode_token


class JWTAuthMiddleware:
    """
    Идентифицирует пользователя из заголовка:
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
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.user_id = None
        request.roles = []

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer ") :]
            try:
                payload = decode_token(token)
                if payload.get("type") == "access":
                    request.user_id = int(payload["sub"])
                    request.roles = payload.get("roles", [])
            except jwt.ExpiredSignatureError:
                pass
            except jwt.InvalidTokenError:
                pass

        return self.get_response(request)
