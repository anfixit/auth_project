from django.urls import path

from apps.mock_views.views import (
    orders_list_view,
    product_detail_view,
    products_list_view,
    shops_list_view,
)

urlpatterns = [
    path(
        "products/",
        products_list_view,
        name="mock-products",
    ),
    path(
        "products/<int:product_id>/",
        product_detail_view,
        name="mock-product-detail",
    ),
    path(
        "orders/",
        orders_list_view,
        name="mock-orders",
    ),
    path(
        "shops/",
        shops_list_view,
        name="mock-shops",
    ),
]
