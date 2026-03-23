"""Конфигурация приложения users."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Конфигурация приложения управления пользователями."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    label = 'users'
