import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from apps.access.models import (
    AccessRule,
    BusinessElement,
    Role,
    UserRole,
)
from apps.access.serializers import (
    AccessRuleSerializer,
    BusinessElementSerializer,
    RoleSerializer,
    UserRoleSerializer,
)
from apps.access.services import invalidate_permission_cache
from apps.auth_core.permissions import has_permission


def _json_body(request: HttpRequest) -> dict:
    """Безопасно распарсить JSON-тело запроса.

    Returns:
        Словарь с данными запроса или пустой словарь
        если тело невалидно.
    """
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


@require_http_methods(["GET"])
@has_permission("access_rules", "read_all")
def roles_list_view(request: HttpRequest) -> JsonResponse:
    """Вернуть список всех ролей.

    GET /api/v1/access/roles/
    Требует право: access_rules.read_all
    """
    roles = Role.objects.all()
    return JsonResponse(
        RoleSerializer(roles, many=True).data,
        safe=False,
    )


@require_http_methods(["POST"])
@has_permission("access_rules", "create")
def roles_create_view(request: HttpRequest) -> JsonResponse:
    """Создать новую роль.

    POST /api/v1/access/roles/create/
    Требует право: access_rules.create
    """
    serializer = RoleSerializer(data=_json_body(request))
    if not serializer.is_valid():
        return JsonResponse(
            {
                "detail": "Validation error.",
                "errors": serializer.errors,
            },
            status=400,
        )
    role = serializer.save()
    return JsonResponse(RoleSerializer(role).data, status=201)


@require_http_methods(["DELETE"])
@has_permission("access_rules", "delete_all")
def roles_delete_view(
    request: HttpRequest,
    role_id: int,
) -> JsonResponse:
    """Удалить роль по id.

    DELETE /api/v1/access/roles/<role_id>/delete/
    Требует право: access_rules.delete_all
    """
    try:
        role = Role.objects.get(pk=role_id)
    except Role.DoesNotExist:
        return JsonResponse(
            {"detail": "Role not found."},
            status=404,
        )
    role.delete()
    invalidate_permission_cache()
    return JsonResponse({"detail": "Role deleted."})


@require_http_methods(["GET"])
@has_permission("access_rules", "read_all")
def elements_list_view(request: HttpRequest) -> JsonResponse:
    """Вернуть список всех бизнес-объектов.

    GET /api/v1/access/elements/
    Требует право: access_rules.read_all
    """
    elements = BusinessElement.objects.all()
    return JsonResponse(
        BusinessElementSerializer(elements, many=True).data,
        safe=False,
    )


@require_http_methods(["GET"])
@has_permission("access_rules", "read_all")
def rules_list_view(request: HttpRequest) -> JsonResponse:
    """Вернуть полную матрицу прав доступа.

    GET /api/v1/access/rules/
    Требует право: access_rules.read_all
    """
    rules = AccessRule.objects.select_related("role", "element").all()
    return JsonResponse(
        AccessRuleSerializer(rules, many=True).data,
        safe=False,
    )


@require_http_methods(["POST"])
@has_permission("access_rules", "create")
def rules_create_view(request: HttpRequest) -> JsonResponse:
    """Создать новое правило доступа.

    POST /api/v1/access/rules/create/
    Требует право: access_rules.create
    """
    serializer = AccessRuleSerializer(data=_json_body(request))
    if not serializer.is_valid():
        return JsonResponse(
            {
                "detail": "Validation error.",
                "errors": serializer.errors,
            },
            status=400,
        )
    rule = serializer.save()
    invalidate_permission_cache()
    return JsonResponse(
        AccessRuleSerializer(rule).data,
        status=201,
    )


@require_http_methods(["PATCH"])
@has_permission("access_rules", "update_all")
def rules_update_view(
    request: HttpRequest,
    rule_id: int,
) -> JsonResponse:
    """Обновить правило доступа.

    PATCH /api/v1/access/rules/<rule_id>/update/
    Требует право: access_rules.update_all
    """
    try:
        rule = AccessRule.objects.get(pk=rule_id)
    except AccessRule.DoesNotExist:
        return JsonResponse(
            {"detail": "Rule not found."},
            status=404,
        )
    serializer = AccessRuleSerializer(
        rule,
        data=_json_body(request),
        partial=True,
    )
    if not serializer.is_valid():
        return JsonResponse(
            {
                "detail": "Validation error.",
                "errors": serializer.errors,
            },
            status=400,
        )
    serializer.save()
    invalidate_permission_cache()
    return JsonResponse(serializer.data)


@require_http_methods(["DELETE"])
@has_permission("access_rules", "delete_all")
def rules_delete_view(
    request: HttpRequest,
    rule_id: int,
) -> JsonResponse:
    """Удалить правило доступа.

    DELETE /api/v1/access/rules/<rule_id>/delete/
    Требует право: access_rules.delete_all
    """
    try:
        rule = AccessRule.objects.get(pk=rule_id)
    except AccessRule.DoesNotExist:
        return JsonResponse(
            {"detail": "Rule not found."},
            status=404,
        )
    rule.delete()
    invalidate_permission_cache()
    return JsonResponse({"detail": "Rule deleted."})


@require_http_methods(["GET"])
@has_permission("users", "read_all")
def user_roles_list_view(request: HttpRequest) -> JsonResponse:
    """Вернуть список всех назначений ролей пользователям.

    GET /api/v1/access/user-roles/
    Требует право: users.read_all
    """
    user_roles = UserRole.objects.select_related("user", "role").all()
    return JsonResponse(
        UserRoleSerializer(user_roles, many=True).data,
        safe=False,
    )


@require_http_methods(["POST"])
@has_permission("access_rules", "create")
def user_roles_assign_view(
    request: HttpRequest,
) -> JsonResponse:
    """Назначить роль пользователю.

    POST /api/v1/access/user-roles/assign/
    Требует право: access_rules.create
    """
    serializer = UserRoleSerializer(data=_json_body(request))
    if not serializer.is_valid():
        return JsonResponse(
            {
                "detail": "Validation error.",
                "errors": serializer.errors,
            },
            status=400,
        )
    user_role, created = UserRole.objects.get_or_create(
        user_id=serializer.validated_data["user"].pk,
        role_id=serializer.validated_data["role"].pk,
    )
    invalidate_permission_cache()
    return JsonResponse(
        UserRoleSerializer(user_role).data,
        status=201 if created else 200,
    )


@require_http_methods(["DELETE"])
@has_permission("access_rules", "delete_all")
def user_roles_remove_view(
    request: HttpRequest,
    user_role_id: int,
) -> JsonResponse:
    """Снять роль с пользователя.

    DELETE /api/v1/access/user-roles/<user_role_id>/remove/
    Требует право: access_rules.delete_all
    """
    try:
        user_role = UserRole.objects.get(pk=user_role_id)
    except UserRole.DoesNotExist:
        return JsonResponse(
            {"detail": "UserRole not found."},
            status=404,
        )
    user_role.delete()
    invalidate_permission_cache()
    return JsonResponse({"detail": "Role removed from user."})
