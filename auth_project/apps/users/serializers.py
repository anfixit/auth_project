"""Сериализаторы приложения users."""

__all__ = [
    'LoginSerializer',
    'RefreshTokenSerializer',
    'RegisterSerializer',
    'UpdateProfileSerializer',
    'UserProfileSerializer',
]

from rest_framework import serializers

from apps.users.constants import MIN_PASSWORD_LENGTH
from apps.users.models import User


class RegisterSerializer(serializers.Serializer):
    """Сериализатор регистрации пользователя."""

    email = serializers.EmailField()
    password = serializers.CharField(
        min_length=MIN_PASSWORD_LENGTH,
        write_only=True,
    )
    password_confirm = serializers.CharField(
        write_only=True,
    )
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    patronymic = serializers.CharField(
        max_length=100,
        required=False,
        default='',
    )

    def validate(self, attrs: dict) -> dict:
        """Проверить совпадение паролей.

        Args:
            attrs: Словарь валидируемых полей.

        Returns:
            Валидированный словарь полей.

        Raises:
            ValidationError: Если пароли не совпадают.
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {'password_confirm': 'Passwords do not match.'}
            )
        return attrs


class LoginSerializer(serializers.Serializer):
    """Сериализатор входа в систему."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'patronymic',
            'full_name',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'email',
            'created_at',
            'updated_at',
        )


class UpdateProfileSerializer(serializers.Serializer):
    """Сериализатор обновления профиля пользователя."""

    first_name = serializers.CharField(
        max_length=100,
        required=False,
    )
    last_name = serializers.CharField(
        max_length=100,
        required=False,
    )
    patronymic = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )


class RefreshTokenSerializer(serializers.Serializer):
    """Сериализатор обновления JWT-токена."""

    refresh_token = serializers.CharField()
