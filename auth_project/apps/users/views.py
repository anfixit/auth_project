"""Представления приложения users."""

__all__ = [
    "delete_account_view",
    "profile_view",
    "register_view",
    "update_profile_view",
]

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from apps.auth_core.permissions import login_required
from apps.users.models import User
from apps.users.serializers import (
    RegisterSerializer,
    UpdateProfileSerializer,
    UserProfileSerializer,
)
from apps.users.services import create_user, soft_delete_user
from apps.utils import parse_json_body


def _assign_default_role(user: User) -> None:
    """Назначить роль 'user' при регистрации.

    Args:
        user: Экземпляр созданного пользователя.
    """
    # Отложенный импорт для разрыва циклической зависимости
    # users → access → users
    from apps.access.models import Role, UserRole

    try:
        role = Role.objects.get(name="user")
        UserRole.objects.get_or_create(user=user, role=role)
    except Role.DoesNotExist:
        pass


@require_http_methods(["POST"])
def register_view(request: HttpRequest) -> JsonResponse:
    """Зарегистрировать нового пользователя.

    POST /api/v1/users/register/
    Body: {
        email, password, password_confirm,
        first_name, last_name, patronymic?
    }

    Args:
        request: HTTP-запрос.

    Returns:
        JsonResponse с профилем созданного пользователя.
    """
    serializer = RegisterSerializer(data=parse_json_body(request))
    if not serializer.is_valid():
        return JsonResponse(
            {
                "detail": "Validation error.",
                "errors": serializer.errors,
            },
            status=400,
        )

    data = serializer.validated_data
    try:
        user = create_user(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            patronymic=data.get("patronymic", ""),
        )
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=409)

    _assign_default_role(user)
    return JsonResponse(
        UserProfileSerializer(user).data,
        status=201,
    )


@require_http_methods(["GET"])
@login_required
def profile_view(request: HttpRequest) -> JsonResponse:
    """Вернуть профиль текущего пользователя.

    GET /api/v1/users/me/
    Header: Authorization: Bearer <token>

    Args:
        request: HTTP-запрос с user_id в атрибутах.

    Returns:
        JsonResponse с данными профиля.
    """
    user_id: int = request.user_id
    try:
        user = User.objects.get(pk=user_id, is_active=True)
    except User.DoesNotExist:
        return JsonResponse(
            {"detail": "User not found."},
            status=404,
        )
    return JsonResponse(UserProfileSerializer(user).data)


@require_http_methods(["PATCH"])
@login_required
def update_profile_view(request: HttpRequest) -> JsonResponse:
    """Обновить профиль текущего пользователя.

    PATCH /api/v1/users/me/update/
    Header: Authorization: Bearer <token>
    Body: { first_name?, last_name?, patronymic? }

    Args:
        request: HTTP-запрос с user_id в атрибутах.

    Returns:
        JsonResponse с обновлёнными данными профиля.
    """
    user_id: int = request.user_id  # type: ignore[attr-defined]
    try:
        user = User.objects.get(pk=user_id, is_active=True)
    except User.DoesNotExist:
        return JsonResponse(
            {"detail": "User not found."},
            status=404,
        )

    serializer = UpdateProfileSerializer(
        data=parse_json_body(request),
    )
    if not serializer.is_valid():
        return JsonResponse(
            {
                "detail": "Validation error.",
                "errors": serializer.errors,
            },
            status=400,
        )

    data = serializer.validated_data
    for field in ("first_name", "last_name", "patronymic"):
        if field in data:
            setattr(user, field, data[field])
    user.save(update_fields=[*data.keys(), "updated_at"])
    return JsonResponse(UserProfileSerializer(user).data)


@require_http_methods(["DELETE"])
@login_required
def delete_account_view(request: HttpRequest) -> JsonResponse:
    """Мягкое удаление аккаунта текущего пользователя.

    DELETE /api/v1/users/me/delete/
    Header: Authorization: Bearer <token>

    Устанавливает is_active=False и отзывает все токены.

    Args:
        request: HTTP-запрос с user_id в атрибутах.

    Returns:
        JsonResponse с подтверждением удаления.
    """
    user_id: int = request.user_id

    from apps.auth_core.models import RefreshToken

    RefreshToken.objects.filter(user_id=user_id).delete()
    soft_delete_user(user_id)
    return JsonResponse(
        {"detail": "Account deactivated successfully."},
        status=200,
    )
