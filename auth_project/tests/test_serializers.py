"""Тесты для сериализаторов приложения users."""

import pytest

from apps.users.constants import MIN_PASSWORD_LENGTH
from apps.users.serializers import (
    LoginSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    UpdateProfileSerializer,
    UserProfileSerializer,
)


class TestRegisterSerializer:
    def test_valid_data_passes(self):
        """Валидные данные проходят сериализацию."""
        serializer = RegisterSerializer(
            data={
                'email': 'test@example.com',
                'password': 'TestPass1!',
                'password_confirm': 'TestPass1!',
                'first_name': 'Ivan',
                'last_name': 'Petrov',
            }
        )

        assert serializer.is_valid()

    def test_password_mismatch_fails(self):
        """Несовпадение паролей — ошибка валидации."""
        serializer = RegisterSerializer(
            data={
                'email': 'test@example.com',
                'password': 'TestPass1!',
                'password_confirm': 'OtherPass1!',
                'first_name': 'Ivan',
                'last_name': 'Petrov',
            }
        )

        assert not serializer.is_valid()
        assert 'password_confirm' in serializer.errors

    def test_short_password_fails(self):
        """Пароль короче минимума — ошибка валидации."""
        short = 'x' * (MIN_PASSWORD_LENGTH - 1)
        serializer = RegisterSerializer(
            data={
                'email': 'test@example.com',
                'password': short,
                'password_confirm': short,
                'first_name': 'Ivan',
                'last_name': 'Petrov',
            }
        )

        assert not serializer.is_valid()

    def test_invalid_email_fails(self):
        """Невалидный email — ошибка валидации."""
        serializer = RegisterSerializer(
            data={
                'email': 'not-an-email',
                'password': 'TestPass1!',
                'password_confirm': 'TestPass1!',
                'first_name': 'Ivan',
                'last_name': 'Petrov',
            }
        )

        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_patronymic_optional(self):
        """Отчество не обязательно."""
        serializer = RegisterSerializer(
            data={
                'email': 'test@example.com',
                'password': 'TestPass1!',
                'password_confirm': 'TestPass1!',
                'first_name': 'Ivan',
                'last_name': 'Petrov',
            }
        )

        assert serializer.is_valid()
        assert serializer.validated_data['patronymic'] == ''

    def test_missing_required_fields_fails(self):
        """Отсутствие обязательных полей — ошибка."""
        serializer = RegisterSerializer(data={})

        assert not serializer.is_valid()
        for field in ('email', 'password', 'first_name', 'last_name'):
            assert field in serializer.errors


class TestLoginSerializer:
    def test_valid_data_passes(self):
        """Валидные данные проходят."""
        serializer = LoginSerializer(
            data={
                'email': 'test@example.com',
                'password': 'pass',
            }
        )

        assert serializer.is_valid()

    def test_missing_email_fails(self):
        """Отсутствие email — ошибка."""
        serializer = LoginSerializer(data={'password': 'pass'})

        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_missing_password_fails(self):
        """Отсутствие password — ошибка."""
        serializer = LoginSerializer(data={'email': 'test@example.com'})

        assert not serializer.is_valid()
        assert 'password' in serializer.errors


class TestUpdateProfileSerializer:
    def test_all_fields_optional(self):
        """Все поля необязательны — пустой запрос валиден."""
        serializer = UpdateProfileSerializer(data={})

        assert serializer.is_valid()

    def test_first_name_update(self):
        """Обновление только first_name проходит."""
        serializer = UpdateProfileSerializer(data={'first_name': 'NewName'})

        assert serializer.is_valid()
        assert serializer.validated_data['first_name'] == 'NewName'

    def test_patronymic_can_be_blank(self):
        """Отчество может быть пустой строкой."""
        serializer = UpdateProfileSerializer(data={'patronymic': ''})

        assert serializer.is_valid()


class TestRefreshTokenSerializer:
    def test_valid_token_passes(self):
        """Строка refresh_token проходит валидацию."""
        serializer = RefreshTokenSerializer(
            data={'refresh_token': 'some.token.value'}
        )

        assert serializer.is_valid()

    def test_missing_token_fails(self):
        """Отсутствие refresh_token — ошибка."""
        serializer = RefreshTokenSerializer(data={})

        assert not serializer.is_valid()
        assert 'refresh_token' in serializer.errors


@pytest.mark.django_db
class TestUserProfileSerializer:
    def test_serializes_user(self, admin_user):
        """Сериализует пользователя корректно."""
        serializer = UserProfileSerializer(admin_user)
        data = serializer.data

        assert data['email'] == 'admin@example.com'
        assert 'full_name' in data
        assert 'password' not in data

    def test_read_only_fields_not_writable(self, admin_user):
        """id, email, created_at, updated_at — только для чтения."""
        serializer = UserProfileSerializer(
            admin_user,
            data={
                'id': 999,
                'email': 'hacked@example.com',
                'first_name': 'New',
                'last_name': 'Name',
            },
            partial=True,
        )
        serializer.is_valid()

        assert 'id' not in serializer.validated_data
        assert 'email' not in serializer.validated_data
