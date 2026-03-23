"""Тесты для apps/mock_views/views.py."""

import pytest
from django.test import RequestFactory

from apps.access.models import AccessRule, BusinessElement, Role
from apps.mock_views.views import (
    orders_list_view,
    product_detail_view,
    products_list_view,
    shops_list_view,
)


@pytest.fixture
def factory() -> RequestFactory:
    """Фабрика HTTP-запросов."""
    return RequestFactory()


@pytest.fixture
def setup_permissions(db):
    """Создать роли и права для mock-объектов."""
    role_admin = Role.objects.create(name='admin')
    role_user = Role.objects.create(name='user')

    for element_name in ('products', 'orders', 'shops'):
        element = BusinessElement.objects.create(name=element_name)
        AccessRule.objects.create(
            role=role_admin,
            element=element,
            read=True,
            read_all=True,
        )
        AccessRule.objects.create(
            role=role_user,
            element=element,
            read=True,
            read_all=False,
        )

    return role_admin, role_user


def _get(factory, url, user_id=None, roles=None):
    """Создать GET-запрос с auth-атрибутами."""
    request = factory.get(url)
    request.user_id = user_id
    request.roles = roles or []
    return request


@pytest.mark.django_db
class TestProductsListView:
    def test_returns_products_for_admin(
        self,
        factory,
        setup_permissions,
    ):
        """Возвращает список товаров для admin."""
        request = _get(
            factory,
            '/api/v1/mock/products/',
            user_id=1,
            roles=['admin'],
        )

        response = products_list_view(request)

        assert response.status_code == 200

    def test_returns_401_if_not_authenticated(
        self,
        factory,
        setup_permissions,
    ):
        """Возвращает 401 если не авторизован."""
        request = _get(
            factory,
            '/api/v1/mock/products/',
            user_id=None,
        )

        response = products_list_view(request)

        assert response.status_code == 401

    def test_returns_403_without_read_all(
        self,
        factory,
        setup_permissions,
    ):
        """Возвращает 403 если нет права read_all."""
        request = _get(
            factory,
            '/api/v1/mock/products/',
            user_id=1,
            roles=['user'],
        )

        response = products_list_view(request)

        assert response.status_code == 403


@pytest.mark.django_db
class TestProductDetailView:
    def test_admin_can_see_any_product(
        self,
        factory,
        setup_permissions,
    ):
        """Admin видит любой товар."""
        request = _get(
            factory,
            '/api/v1/mock/products/1/',
            user_id=99,
            roles=['admin'],
        )

        response = product_detail_view(request, product_id=1)

        assert response.status_code == 200

    def test_user_can_see_own_product(
        self,
        factory,
        setup_permissions,
    ):
        """User видит только свой товар (owner_id == user_id)."""
        # product_id=1 имеет owner_id=2
        request = _get(
            factory,
            '/api/v1/mock/products/1/',
            user_id=2,
            roles=['user'],
        )

        response = product_detail_view(request, product_id=1)

        assert response.status_code == 200

    def test_user_cannot_see_others_product(
        self,
        factory,
        setup_permissions,
    ):
        """User не видит чужой товар."""
        # product_id=1 имеет owner_id=2, запрашивает user_id=5
        request = _get(
            factory,
            '/api/v1/mock/products/1/',
            user_id=5,
            roles=['user'],
        )

        response = product_detail_view(request, product_id=1)

        assert response.status_code == 403

    def test_returns_404_for_unknown_product(
        self,
        factory,
        setup_permissions,
    ):
        """Возвращает 404 если товар не найден."""
        request = _get(
            factory,
            '/api/v1/mock/products/999/',
            user_id=1,
            roles=['admin'],
        )

        response = product_detail_view(request, product_id=999)

        assert response.status_code == 404


@pytest.mark.django_db
class TestOrdersListView:
    def test_returns_orders_for_admin(
        self,
        factory,
        setup_permissions,
    ):
        """Возвращает список заказов для admin."""
        request = _get(
            factory,
            '/api/v1/mock/orders/',
            user_id=1,
            roles=['admin'],
        )

        response = orders_list_view(request)

        assert response.status_code == 200

    def test_returns_403_without_read_all(
        self,
        factory,
        setup_permissions,
    ):
        """Возвращает 403 если нет права read_all."""
        request = _get(
            factory,
            '/api/v1/mock/orders/',
            user_id=1,
            roles=['user'],
        )

        response = orders_list_view(request)

        assert response.status_code == 403


@pytest.mark.django_db
class TestShopsListView:
    def test_returns_shops_for_admin(
        self,
        factory,
        setup_permissions,
    ):
        """Возвращает список магазинов для admin."""
        request = _get(
            factory,
            '/api/v1/mock/shops/',
            user_id=1,
            roles=['admin'],
        )

        response = shops_list_view(request)

        assert response.status_code == 200

    def test_returns_403_without_read_all(
        self,
        factory,
        setup_permissions,
    ):
        """Возвращает 403 если нет права read_all."""
        request = _get(
            factory,
            '/api/v1/mock/shops/',
            user_id=1,
            roles=['user'],
        )

        response = shops_list_view(request)

        assert response.status_code == 403
