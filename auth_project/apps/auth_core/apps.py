"""Конфигурация приложения auth_core."""

from django.apps import AppConfig


class AuthCoreConfig(AppConfig):
    """Конфигурация приложения JWT-аутентификации."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.auth_core'
    label = 'auth_core'
