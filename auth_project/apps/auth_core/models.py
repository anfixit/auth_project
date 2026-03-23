"""Модели приложения auth_core."""

__all__ = ["RefreshToken"]

from django.db import models

from apps.users.models import User


class RefreshToken(models.Model):
    """Хранит выданные refresh-токены.

    При logout токен удаляется —
    повторный refresh становится невозможен.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="refresh_tokens",
    )
    token = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "refresh_tokens"
        verbose_name = "Refresh Token"
        verbose_name_plural = "Refresh Tokens"

    def __str__(self) -> str:
        return f"RefreshToken(user={self.user_id})"
