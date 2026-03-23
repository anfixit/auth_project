import jwt
import pytest

from apps.auth_core.tokens import (
    decode_token,
    generate_access_token,
    generate_refresh_token,
)


@pytest.mark.django_db
class TestAccessToken:
    def test_contains_user_id_and_roles(self):
        """Access token содержит user_id и roles в payload."""
        token = generate_access_token(42, ["admin", "user"])
        payload = decode_token(token)

        assert payload["sub"] == "42"
        assert payload["roles"] == ["admin", "user"]
        assert payload["type"] == "access"

    def test_does_not_contain_sensitive_data(self):
        """Payload не содержит чувствительных данных."""
        token = generate_access_token(1, ["user"])
        payload = decode_token(token)

        assert "password" not in payload
        assert "email" not in payload

    def test_empty_roles_allowed(self):
        """Токен можно создать с пустым списком ролей."""
        token = generate_access_token(1, [])
        payload = decode_token(token)

        assert payload["roles"] == []


@pytest.mark.django_db
class TestRefreshToken:
    def test_contains_correct_type(self):
        """Refresh token имеет type=refresh."""
        token = generate_refresh_token(7)
        payload = decode_token(token)

        assert payload["sub"] == "7"
        assert payload["type"] == "refresh"


@pytest.mark.django_db
class TestDecodeToken:
    def test_raises_on_invalid_token(self):
        """Невалидный токен вызывает InvalidTokenError."""
        with pytest.raises(jwt.InvalidTokenError):
            decode_token("not.a.valid.token")

    def test_raises_on_tampered_token(self):
        """Изменённый токен вызывает InvalidTokenError."""
        token = generate_access_token(1, ["user"])
        tampered = token[:-5] + "XXXXX"

        with pytest.raises(jwt.InvalidTokenError):
            decode_token(tampered)
