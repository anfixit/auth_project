"""Тесты для apps/users/views.py."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from django.test import RequestFactory

from apps.auth_core.models import RefreshToken
from apps.users.services import create_user
from apps.users.views import (
    delete_account_view,
    profile_view,
    register_view,
    update_profile_view,
)


@pytest.fixture
def factory() -> RequestFactory:
    """Фабрика HTTP-запросов."""
    return RequestFactory()


@pytest.fixture
def user(db):
    """Создать тестового пользователя."""
    return create_user(
        email='user@example.com',
        password='UserPass1!',
        first_name='Ivan',
        last_name='Petrov',
        patronymic='Ivanovich',
    )


def _post_json(factory, url, data, user_id=None, roles=None):
    """Создать POST-запрос с JSON-телом."""
    request = factory.post(
        url,
        data=json.dumps(data),
        content_type='application/json',
    )
    request.user_id = user_id
    request.roles = roles or []
    return request


def _patch_json(factory, url, data, user_id=None, roles=None):
    """Создать PATCH-запрос с JSON-телом."""
    request = factory.patch(
        url,
        data=json.dumps(data),
        content_type='application/json',
    )
    request.user_id = user_id
    request.roles = roles or []
    return request


@pytest.mark.django_db
class TestRegisterView:
    def test_creates_user_and_returns_201(self, factory, db):
        """Создаёт пользователя и возвращает 201."""
        request = _post_json(
            factory,
            '/api/v1/users/register/',
            {
                'email': 'new@example.com',
                'password': 'NewPass1!',
                'password_confirm': 'NewPass1!',
                'first_name': 'Anna',
                'last_name': 'Ivanova',
            },
        )

        response = register_view(request)
        data = json.loads(response.content)

        assert response.status_code == 201
        assert data['email'] == 'new@example.com'
        assert data['first_name'] == 'Anna'

    def test_returns_400_if_passwords_dont_match(
        self,
        factory,
        db,
    ):
        """Возвращает 400 если пароли не совпадают."""
        request = _post_json(
            factory,
            '/api/v1/users/register/',
            {
                'email': 'new@example.com',
                'password': 'NewPass1!',
                'password_confirm': 'Different1!',
                'first_name': 'Anna',
                'last_name': 'Ivanova',
            },
        )

        response = register_view(request)

        assert response.status_code == 400

    def test_returns_409_on_duplicate_email(
        self,
        factory,
        user,
    ):
        """Возвращает 409 при попытке зарегистрировать занятый email."""
        request = _post_json(
            factory,
            '/api/v1/users/register/',
            {
                'email': 'user@example.com',
                'password': 'NewPass1!',
                'password_confirm': 'NewPass1!',
                'first_name': 'Anna',
                'last_name': 'Ivanova',
            },
        )

        response = register_view(request)

        assert response.status_code == 409

    def test_returns_400_on_missing_fields(self, factory, db):
        """Возвращает 400 при отсутствии обязательных полей."""
        request = _post_json(
            factory,
            '/api/v1/users/register/',
            {'email': 'new@example.com'},
        )

        response = register_view(request)

        assert response.status_code == 400

    def test_returns_400_on_short_password(self, factory, db):
        """Возвращает 400 если пароль короче 8 символов."""
        request = _post_json(
            factory,
            '/api/v1/users/register/',
            {
                'email': 'new@example.com',
                'password': 'short',
                'password_confirm': 'short',
                'first_name': 'Anna',
                'last_name': 'Ivanova',
            },
        )

        response = register_view(request)

        assert response.status_code == 400

    def test_creates_with_optional_patronymic(self, factory, db):
        """Создаёт пользователя с отчеством."""
        request = _post_json(
            factory,
            '/api/v1/users/register/',
            {
                'email': 'pat@example.com',
                'password': 'NewPass1!',
                'password_confirm': 'NewPass1!',
                'first_name': 'Ivan',
                'last_name': 'Petrov',
                'patronymic': 'Ivanovich',
            },
        )

        response = register_view(request)
        data = json.loads(response.content)

        assert response.status_code == 201
        assert data['patronymic'] == 'Ivanovich'


@pytest.mark.django_db
class TestProfileView:
    def test_returns_profile_for_authenticated_user(
        self,
        factory,
        user,
    ):
        """Возвращает профиль авторизованного пользователя."""
        request = factory.get('/api/v1/users/me/')
        request.user_id = user.pk
        request.roles = []

        response = profile_view(request)
        data = json.loads(response.content)

        assert response.status_code == 200
        assert data['email'] == 'user@example.com'
        assert data['first_name'] == 'Ivan'

    def test_returns_401_if_not_authenticated(self, factory, db):
        """Возвращает 401 если пользователь не авторизован."""
        request = factory.get('/api/v1/users/me/')
        request.user_id = None
        request.roles = []

        response = profile_view(request)

        assert response.status_code == 401

    def test_returns_404_for_nonexistent_user(self, factory, db):
        """Возвращает 404 если пользователь не найден."""
        request = factory.get('/api/v1/users/me/')
        request.user_id = 99999
        request.roles = []

        response = profile_view(request)

        assert response.status_code == 404

    def test_returns_404_for_inactive_user(self, factory, user):
        """Возвращает 404 для деактивированного пользователя."""
        user.is_active = False
        user.save()

        request = factory.get('/api/v1/users/me/')
        request.user_id = user.pk
        request.roles = []

        response = profile_view(request)

        assert response.status_code == 404


@pytest.mark.django_db
class TestUpdateProfileView:
    def test_updates_first_name(self, factory, user):
        """Обновляет имя пользователя."""
        request = _patch_json(
            factory,
            '/api/v1/users/me/update/',
            {'first_name': 'Petr'},
            user_id=user.pk,
        )

        response = update_profile_view(request)
        data = json.loads(response.content)

        assert response.status_code == 200
        assert data['first_name'] == 'Petr'

    def test_updates_multiple_fields(self, factory, user):
        """Обновляет несколько полей одновременно."""
        request = _patch_json(
            factory,
            '/api/v1/users/me/update/',
            {'first_name': 'Petr', 'last_name': 'Sidorov'},
            user_id=user.pk,
        )

        response = update_profile_view(request)
        data = json.loads(response.content)

        assert response.status_code == 200
        assert data['first_name'] == 'Petr'
        assert data['last_name'] == 'Sidorov'

    def test_returns_401_if_not_authenticated(self, factory, db):
        """Возвращает 401 если пользователь не авторизован."""
        request = _patch_json(
            factory,
            '/api/v1/users/me/update/',
            {'first_name': 'Petr'},
            user_id=None,
        )

        response = update_profile_view(request)

        assert response.status_code == 401

    def test_returns_404_for_nonexistent_user(self, factory, db):
        """Возвращает 404 если пользователь не найден."""
        request = _patch_json(
            factory,
            '/api/v1/users/me/update/',
            {'first_name': 'Petr'},
            user_id=99999,
        )

        response = update_profile_view(request)

        assert response.status_code == 404


@pytest.mark.django_db
class TestDeleteAccountView:
    def test_deactivates_user(self, factory, user):
        """Устанавливает is_active=False."""
        request = factory.delete('/api/v1/users/me/delete/')
        request.user_id = user.pk
        request.roles = []

        response = delete_account_view(request)

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.is_active is False

    def test_revokes_refresh_tokens(self, factory, user):
        """Отзывает все refresh_tokens пользователя."""
        RefreshToken.objects.create(
            user=user,
            token='token-1',
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )

        request = factory.delete('/api/v1/users/me/delete/')
        request.user_id = user.pk
        request.roles = []

        delete_account_view(request)

        assert not RefreshToken.objects.filter(user=user).exists()

    def test_returns_401_if_not_authenticated(self, factory, db):
        """Возвращает 401 если пользователь не авторизован."""
        request = factory.delete('/api/v1/users/me/delete/')
        request.user_id = None
        request.roles = []

        response = delete_account_view(request)

        assert response.status_code == 401
