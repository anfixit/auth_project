"""Тесты для apps/auth_core/permissions.py и check_permission."""

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from apps.access.models import AccessRule
from apps.access.services import check_permission
from apps.auth_core.middleware import JWTAuthMiddleware
from apps.auth_core.permissions import has_permission, login_required
from apps.auth_core.tokens import generate_access_token


@pytest.fixture
def factory() -> RequestFactory:
    """Фабрика HTTP-запросов."""
    return RequestFactory()


# ─── check_permission ────────────────────────────────────────────


@pytest.mark.django_db
class TestCheckPermission:
    def test_returns_true_when_role_has_permission(self, admin_rule):
        """Возвращает True если роль имеет право."""
        result = check_permission(['admin'], 'products', 'read_all')

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

        result = check_permission(['user'], 'products', 'read_all')

        assert result is False

    def test_returns_false_for_empty_roles(self):
        """Возвращает False для пустого списка ролей."""
        result = check_permission([], 'products', 'read_all')

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

        result = check_permission(['user', 'admin'], 'products', 'read_all')

        assert result is True

    def test_returns_false_for_unknown_element(self, admin_rule):
        """Возвращает False для несуществующего объекта."""
        result = check_permission(['admin'], 'nonexistent', 'read')

        assert result is False

    def test_result_cached_on_second_call(self, admin_rule):
        """Повторный вызов возвращает результат из кеша."""
        result_first = check_permission(['admin'], 'products', 'read_all')
        result_second = check_permission(['admin'], 'products', 'read_all')

        assert result_first is True
        assert result_second is True


# ─── JWTAuthMiddleware ────────────────────────────────────────────


@pytest.mark.django_db
class TestJWTMiddleware:
    def test_valid_token_sets_user_id_and_roles(self):
        """Валидный токен устанавливает user_id и roles."""
        token = generate_access_token(99, ['admin'])
        factory = RequestFactory()
        request = factory.get(
            '/',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        middleware = JWTAuthMiddleware(lambda req: HttpResponse())
        middleware(request)

        assert request.user_id == 99
        assert request.roles == ['admin']

    def test_missing_token_leaves_user_id_none(self):
        """Без токена user_id остаётся None."""
        factory = RequestFactory()
        request = factory.get('/')

        middleware = JWTAuthMiddleware(lambda req: HttpResponse())
        middleware(request)

        assert request.user_id is None
        assert request.roles == []

    def test_invalid_token_leaves_user_id_none(self):
        """Невалидный токен оставляет user_id None."""
        factory = RequestFactory()
        request = factory.get(
            '/',
            HTTP_AUTHORIZATION='Bearer invalid.token.here',
        )

        middleware = JWTAuthMiddleware(lambda req: HttpResponse())
        middleware(request)

        assert request.user_id is None

    def test_refresh_token_not_accepted_as_access(self):
        """Refresh-токен не принимается как access."""
        from apps.auth_core.tokens import generate_refresh_token

        token = generate_refresh_token(1)
        factory = RequestFactory()
        request = factory.get(
            '/',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        middleware = JWTAuthMiddleware(lambda req: HttpResponse())
        middleware(request)

        assert request.user_id is None

    def test_missing_bearer_prefix_ignored(self):
        """Заголовок без префикса Bearer игнорируется."""
        token = generate_access_token(1, ['user'])
        factory = RequestFactory()
        request = factory.get(
            '/',
            HTTP_AUTHORIZATION=token,
        )

        middleware = JWTAuthMiddleware(lambda req: HttpResponse())
        middleware(request)

        assert request.user_id is None


# ─── login_required ──────────────────────────────────────────────


class TestLoginRequired:
    def test_returns_401_when_not_authenticated(self, factory):
        """Возвращает 401 если user_id не установлен."""

        @login_required
        def view(request):
            return HttpResponse('ok')

        request = factory.get('/')
        request.user_id = None
        request.roles = []

        response = view(request)

        assert response.status_code == 401

    def test_passes_through_when_authenticated(self, factory):
        """Пропускает запрос если user_id установлен."""

        @login_required
        def view(request):
            return HttpResponse('ok')

        request = factory.get('/')
        request.user_id = 1
        request.roles = ['user']

        response = view(request)

        assert response.status_code == 200

    def test_preserves_view_response(self, factory):
        """Возвращает ответ оригинальной view."""

        @login_required
        def view(request):
            return HttpResponse('secret', status=200)

        request = factory.get('/')
        request.user_id = 42
        request.roles = []

        response = view(request)

        assert response.content == b'secret'


# ─── has_permission ───────────────────────────────────────────────


@pytest.mark.django_db
class TestHasPermission:
    def test_returns_401_when_not_authenticated(self, factory):
        """Возвращает 401 если пользователь не авторизован."""

        @has_permission('products', 'read_all')
        def view(request):
            return HttpResponse('ok')

        request = factory.get('/')
        request.user_id = None
        request.roles = []

        response = view(request)

        assert response.status_code == 401

    def test_returns_403_when_no_permission(
        self, factory, role_user, element_products
    ):
        """Возвращает 403 если права нет."""
        AccessRule.objects.create(
            role=role_user,
            element=element_products,
            read_all=False,
        )

        @has_permission('products', 'read_all')
        def view(request):
            return HttpResponse('ok')

        request = factory.get('/')
        request.user_id = 1
        request.roles = ['user']

        response = view(request)

        assert response.status_code == 403

    def test_passes_through_when_permitted(self, factory, admin_rule):
        """Пропускает запрос если право есть."""

        @has_permission('products', 'read_all')
        def view(request):
            return HttpResponse('ok')

        request = factory.get('/')
        request.user_id = 1
        request.roles = ['admin']

        response = view(request)

        assert response.status_code == 200

    def test_passes_kwargs_to_view(self, factory, admin_rule):
        """Передаёт kwargs в оригинальную view."""

        @has_permission('products', 'read_all')
        def view(request, pk):
            return HttpResponse(str(pk))

        request = factory.get('/')
        request.user_id = 1
        request.roles = ['admin']

        response = view(request, pk=42)

        assert response.content == b'42'
