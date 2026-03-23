"""Конфигурация приложения access."""

from django.apps import AppConfig


class AccessConfig(AppConfig):
    """Конфигурация приложения управления доступом."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.access'
    label = 'access'
