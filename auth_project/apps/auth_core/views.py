import json
from datetime import UTC, datetime, timedelta

import jwt
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from apps.auth_core.models import RefreshToken
from apps.auth_core.permissions import login_required
from apps.auth_core.tokens import (
    decode_token,
    generate_access_token,
    generate_refresh_token,
)
from apps.users.serializers import (
    LoginSerializer,
    RefreshTokenSerializer,
)
from apps.users.services import authenticate_user, get_role_names


def _json_body(request: HttpRequest) -> dict:
    """Безопасно распарсить JSON-тело запроса.

    Returns:
        Словарь с данными или пустой словарь
        если тело невалидно.
    """
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


@require_http_methods(["POST"])
def login_view(request: HttpRequest) -> JsonResponse:
    """Аутентифицировать пользователя и выдать токены.

    POST /api/v1/auth/login/
    Body: { email, password }

    Returns:
        JsonResponse с access_token и refresh_token.
    """
    serializer = LoginSerializer(data=_json_body(request))
    if not serializer.is_valid():
        return JsonResponse(
            {
                "detail": "Validation error.",
                "errors": serializer.errors,
            },
            status=400,
        )

    data = serializer.validated_data
    user = authenticate_user(data["email"], data["password"])
    if user is None:
        return JsonResponse(
            {"detail": "Invalid email or password."},
            status=401,
        )

    role_names = get_role_names(user.pk)
    access_token = generate_access_token(user.pk, role_names)
    refresh_token = generate_refresh_token(user.pk)

    expires_at = datetime.now(UTC) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    RefreshToken.objects.create(
        user=user,
        token=refresh_token,
        expires_at=expires_at,
    )

    return JsonResponse(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
        }
    )


@require_http_methods(["POST"])
@login_required
def logout_view(request: HttpRequest) -> JsonResponse:
    """Выйти из системы и отозвать все refresh токены.

    POST /api/v1/auth/logout/
    Header: Authorization: Bearer <access_token>

    Returns:
        JsonResponse с количеством отозванных токенов.
    """
    user_id: int = request.user_id  # type: ignore[attr-defined]
    deleted_count, _ = RefreshToken.objects.filter(user_id=user_id).delete()

    return JsonResponse(
        {
            "detail": "Logged out successfully.",
            "tokens_revoked": deleted_count,
        }
    )


@require_http_methods(["POST"])
def refresh_view(request: HttpRequest) -> JsonResponse:
    """Обновить access token по refresh token.

    POST /api/v1/auth/refresh/
    Body: { refresh_token }

    Returns:
        JsonResponse с новым access_token.
    """
    serializer = RefreshTokenSerializer(data=_json_body(request))
    if not serializer.is_valid():
        return JsonResponse(
            {
                "detail": "Validation error.",
                "errors": serializer.errors,
            },
            status=400,
        )

    raw_token: str = serializer.validated_data["refresh_token"]

    try:
        payload = decode_token(raw_token)
    except jwt.ExpiredSignatureError:
        return JsonResponse(
            {"detail": "Refresh token expired."},
            status=401,
        )
    except jwt.InvalidTokenError:
        return JsonResponse(
            {"detail": "Invalid refresh token."},
            status=401,
        )

    if payload.get("type") != "refresh":
        return JsonResponse(
            {"detail": "Invalid token type."},
            status=401,
        )

    try:
        stored = RefreshToken.objects.select_related("user").get(
            token=raw_token
        )
    except RefreshToken.DoesNotExist:
        return JsonResponse(
            {"detail": "Refresh token not found or revoked."},
            status=401,
        )

    if not stored.user.is_active:
        return JsonResponse(
            {"detail": "User account is disabled."},
            status=401,
        )

    role_names = get_role_names(stored.user.pk)
    new_access = generate_access_token(stored.user.pk, role_names)

    return JsonResponse(
        {
            "access_token": new_access,
            "token_type": "Bearer",
        }
    )
