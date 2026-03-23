"""
Mock views — вымышленные бизнес-объекты для демонстрации
работы системы авторизации. Таблицы в БД не создаются.
"""

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods

from apps.access.services import check_permission
from apps.auth_core.permissions import has_permission

_MOCK_PRODUCTS = [
    {
        'id': 1,
        'name': 'Laptop Pro 16',
        'price': 199900,
        'owner_id': 2,
    },
    {
        'id': 2,
        'name': 'Wireless Mouse',
        'price': 2990,
        'owner_id': 3,
    },
    {
        'id': 3,
        'name': 'Mechanical Keyboard',
        'price': 8990,
        'owner_id': 2,
    },
]

_MOCK_ORDERS = [
    {
        'id': 1,
        'product_id': 1,
        'quantity': 2,
        'status': 'pending',
        'owner_id': 4,
    },
    {
        'id': 2,
        'product_id': 3,
        'quantity': 1,
        'status': 'completed',
        'owner_id': 5,
    },
]

_MOCK_SHOPS = [
    {
        'id': 1,
        'name': 'TechZone',
        'city': 'Moscow',
        'owner_id': 2,
    },
    {
        'id': 2,
        'name': 'Digital World',
        'city': 'SPb',
        'owner_id': 3,
    },
]


@require_http_methods(['GET'])
@has_permission('products', 'read_all')
def products_list_view(request: HttpRequest) -> JsonResponse:
    """Вернуть список всех товаров.

    GET /api/v1/mock/products/
    Требует право: products.read_all
    """
    return JsonResponse({'results': _MOCK_PRODUCTS})


@require_http_methods(['GET'])
@has_permission('products', 'read')
def product_detail_view(
    request: HttpRequest,
    product_id: int,
) -> JsonResponse:
    """Вернуть товар по id.

    GET /api/v1/mock/products/<product_id>/
    Требует право: products.read
    Пользователь с read_all видит любой товар.
    Пользователь с read — только свой (owner_id == user_id).

    Args:
        request: HTTP-запрос с user_id и roles.
        product_id: идентификатор товара.

    Returns:
        JsonResponse с данными товара или ошибкой.
    """
    user_id: int = request.user_id  # type: ignore[attr-defined]
    roles: list[str] = request.roles  # type: ignore[attr-defined]

    product = next(
        (p for p in _MOCK_PRODUCTS if p['id'] == product_id),
        None,
    )
    if product is None:
        return JsonResponse(
            {'detail': 'Product not found.'},
            status=404,
        )

    if check_permission(roles, 'products', 'read_all'):
        return JsonResponse(product)

    # read — только свой объект
    if product['owner_id'] != user_id:
        return JsonResponse(
            {'detail': 'Forbidden.'},
            status=403,
        )

    return JsonResponse(product)


@require_http_methods(['GET'])
@has_permission('orders', 'read_all')
def orders_list_view(request: HttpRequest) -> JsonResponse:
    """Вернуть список всех заказов.

    GET /api/v1/mock/orders/
    Требует право: orders.read_all
    """
    return JsonResponse({'results': _MOCK_ORDERS})


@require_http_methods(['GET'])
@has_permission('shops', 'read_all')
def shops_list_view(request: HttpRequest) -> JsonResponse:
    """Вернуть список всех магазинов.

    GET /api/v1/mock/shops/
    Требует право: shops.read_all
    """
    return JsonResponse({'results': _MOCK_SHOPS})
