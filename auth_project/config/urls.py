"""Корневая конфигурация URL проекта."""

from django.urls import include, path

urlpatterns = [
    path('api/v1/auth/', include('apps.auth_core.urls')),
    path('api/v1/users/', include('apps.users.urls')),
    path('api/v1/access/', include('apps.access.urls')),
    path('api/v1/mock/', include('apps.mock_views.urls')),
]
