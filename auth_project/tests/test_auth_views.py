"""Тесты для apps/auth_core/views.py."""

import json
from datetime import UTC, datetime, timedelta

import pytest
from django.test import RequestFactory

from apps.auth_core.models import RefreshToken
from apps.auth_core.tokens import generate_refresh_token
from apps.auth_core.views import login_view, logout_view, refresh_view
from apps.users.services import create_user


@pytest.fixture
def factory() -> RequestFactory:
    """Фабрика HTTP-запросов."""
    return RequestFactory()


@pytest.fixture
def user(db):
    """Создать тестового пользователя."""
    return create_user(
        email='test@example.com',
        password='TestPass1!',
        first_name='Test',
        last_name='User',
    )


def _post_json(factory, url, data, user_id=None, roles=None):
    """Создать POST-запрос с JSON-телом и атрибутами auth."""
    request = factory.post(
        url,
        data=json.dumps(data),
        content_type='application/json',
    )
    request.user_id = user_id
    request.roles = roles or []
    return request


@pytest.mark.django_db
class TestLoginView:
    def test_returns_tokens_on_valid_credentials(
        self,
        factory,
        user,
    ):
        """Возвращает токены при верных данных."""
        request = _post_json(
            factory,
            '/api/v1/auth/login/',
            {'email': 'test@example.com', 'password': 'TestPass1!'},
        )

        response = login_view(request)
        data = json.loads(response.content)

        assert response.status_code == 200
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert data['token_type'] == 'Bearer'

    def test_creates_refresh_token_in_db(self, factory, user):
        """Создаёт refresh_token в базе данных."""
        request = _post_json(
            factory,
            '/api/v1/auth/login/',
            {'email': 'test@example.com', 'password': 'TestPass1!'},
        )

        login_view(request)

        assert RefreshToken.objects.filter(user=user).exists()

    def test_returns_401_on_wrong_password(self, factory, user):
        """Возвращает 401 при неверном пароле."""
        request = _post_json(
            factory,
            '/api/v1/auth/login/',
            {'email': 'test@example.com', 'password': 'WrongPass!'},
        )

        response = login_view(request)

        assert response.status_code == 401

    def test_returns_401_on_unknown_email(self, factory, db):
        """Возвращает 401 при несуществующем email."""
        request = _post_json(
            factory,
            '/api/v1/auth/login/',
            {'email': 'nobody@example.com', 'password': 'Pass1234!'},
        )

        response = login_view(request)

        assert response.status_code == 401

    def test_returns_400_on_missing_fields(self, factory, db):
        """Возвращает 400 при отсутствии обязательных полей."""
        request = _post_json(
            factory,
            '/api/v1/auth/login/',
            {'email': 'test@example.com'},
        )

        response = login_view(request)

        assert response.status_code == 400

    def test_returns_401_for_inactive_user(self, factory, user):
        """Возвращает 401 для деактивированного пользователя."""
        user.is_active = False
        user.save()

        request = _post_json(
            factory,
            '/api/v1/auth/login/',
            {'email': 'test@example.com', 'password': 'TestPass1!'},
        )

        response = login_view(request)

        assert response.status_code == 401


@pytest.mark.django_db
class TestLogoutView:
    def test_deletes_refresh_tokens(self, factory, user):
        """Удаляет все refresh_tokens пользователя."""
        RefreshToken.objects.create(
            user=user,
            token='some-refresh-token',
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )

        request = factory.post('/api/v1/auth/logout/')
        request.user_id = user.pk
        request.roles = []

        response = logout_view(request)
        data = json.loads(response.content)

        assert response.status_code == 200
        assert data['tokens_revoked'] == 1
        assert not RefreshToken.objects.filter(user=user).exists()

    def test_returns_200_if_no_tokens(self, factory, user):
        """Возвращает 200 если токенов нет."""
        request = factory.post('/api/v1/auth/logout/')
        request.user_id = user.pk
        request.roles = []

        response = logout_view(request)
        data = json.loads(response.content)

        assert response.status_code == 200
        assert data['tokens_revoked'] == 0

    def test_returns_401_if_not_authenticated(self, factory, db):
        """Возвращает 401 если пользователь не авторизован."""
        request = factory.post('/api/v1/auth/logout/')
        request.user_id = None
        request.roles = []

        response = logout_view(request)

        assert response.status_code == 401


@pytest.mark.django_db
class TestRefreshView:
    def test_returns_new_access_token(self, factory, user):
        """Возвращает новый access_token по refresh_token."""
        refresh_token = generate_refresh_token(user.pk)
        RefreshToken.objects.create(
            user=user,
            token=refresh_token,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )

        request = _post_json(
            factory,
            '/api/v1/auth/refresh/',
            {'refresh_token': refresh_token},
        )
        request.user_id = None
        request.roles = []

        response = refresh_view(request)
        data = json.loads(response.content)

        assert response.status_code == 200
        assert 'access_token' in data
        assert data['token_type'] == 'Bearer'

    def test_returns_401_on_invalid_token(self, factory, db):
        """Возвращает 401 при невалидном токене."""
        request = _post_json(
            factory,
            '/api/v1/auth/refresh/',
            {'refresh_token': 'invalid.token.here'},
        )
        request.user_id = None
        request.roles = []

        response = refresh_view(request)

        assert response.status_code == 401

    def test_returns_401_on_revoked_token(self, factory, user):
        """Возвращает 401 если токен отозван (не в БД)."""
        refresh_token = generate_refresh_token(user.pk)

        request = _post_json(
            factory,
            '/api/v1/auth/refresh/',
            {'refresh_token': refresh_token},
        )
        request.user_id = None
        request.roles = []

        response = refresh_view(request)

        assert response.status_code == 401

    def test_returns_401_for_inactive_user(self, factory, user):
        """Возвращает 401 если пользователь деактивирован."""
        refresh_token = generate_refresh_token(user.pk)
        RefreshToken.objects.create(
            user=user,
            token=refresh_token,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        user.is_active = False
        user.save()

        request = _post_json(
            factory,
            '/api/v1/auth/refresh/',
            {'refresh_token': refresh_token},
        )
        request.user_id = None
        request.roles = []

        response = refresh_view(request)

        assert response.status_code == 401

    def test_returns_400_on_missing_field(self, factory, db):
        """Возвращает 400 если refresh_token не передан."""
        request = _post_json(
            factory,
            '/api/v1/auth/refresh/',
            {},
        )
        request.user_id = None
        request.roles = []

        response = refresh_view(request)

        assert response.status_code == 400
