"""Конфигурация приложения mock_views."""

from django.apps import AppConfig


class MockViewsConfig(AppConfig):
    """Конфигурация приложения mock бизнес-объектов."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mock_views'
    label = 'mock_views'
