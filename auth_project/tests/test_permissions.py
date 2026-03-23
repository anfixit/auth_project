import pytest

from apps.access.models import AccessRule
from apps.access.services import check_permission
from apps.auth_core.middleware import JWTAuthMiddleware
from apps.auth_core.tokens import generate_access_token


@pytest.mark.django_db
class TestCheckPermission:
    def test_returns_true_when_role_has_permission(self, admin_rule):
        """Возвращает True если роль имеет право."""
        result = check_permission(["admin"], "products", "read_all")

        assert result is True

    def test_returns_false_when_role_lacks_permission(
        self, role_user, element_products
    ):
        """Возвращает False если роль не имеет права."""
        AccessRule.objects.create(
            role=role_user,
            element=element_products,
            read=True,
            read_all=False,
        )

        result = check_permission(["user"], "products", "read_all")

        assert result is False

    def test_returns_false_for_empty_roles(self):
        """Возвращает False для пустого списка ролей."""
        result = check_permission([], "products", "read_all")

        assert result is False

    def test_returns_true_if_any_role_grants_permission(
        self, admin_rule, role_user, element_products
    ):
        """True если хотя бы одна роль даёт право."""
        AccessRule.objects.create(
            role=role_user,
            element=element_products,
            read_all=False,
        )

        result = check_permission(["user", "admin"], "products", "read_all")

        assert result is True

    def test_returns_false_for_unknown_element(self, admin_rule):
        """Возвращает False для несуществующего объекта."""
        result = check_permission(["admin"], "nonexistent", "read")

        assert result is False


@pytest.mark.django_db
class TestJWTMiddleware:
    def test_valid_token_sets_user_id_and_roles(self):
        """Валидный токен устанавливает user_id и roles."""
        from django.http import HttpResponse
        from django.test import RequestFactory

        token = generate_access_token(99, ["admin"])
        factory = RequestFactory()
        request = factory.get(
            "/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        middleware = JWTAuthMiddleware(lambda req: HttpResponse())
        middleware(request)

        assert request.user_id == 99
        assert request.roles == ["admin"]

    def test_missing_token_leaves_user_id_none(self):
        """Без токена user_id остаётся None."""
        from django.http import HttpResponse
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/")

        middleware = JWTAuthMiddleware(lambda req: HttpResponse())
        middleware(request)

        assert request.user_id is None
        assert request.roles == []

    def test_invalid_token_leaves_user_id_none(self):
        """Невалидный токен оставляет user_id None."""
        from django.http import HttpResponse
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get(
            "/",
            HTTP_AUTHORIZATION="Bearer invalid.token.here",
        )

        middleware = JWTAuthMiddleware(lambda req: HttpResponse())
        middleware(request)

        assert request.user_id is None
