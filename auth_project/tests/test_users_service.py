import pytest

from apps.users.services import (
    authenticate_user,
    create_user,
    soft_delete_user,
)


@pytest.mark.django_db
class TestCreateUser:
    def test_creates_user_with_hashed_password(self):
        """Пароль хранится в хешированном виде."""
        user = create_user(
            email="test@example.com",
            password="SecurePass1!",
            first_name="Ivan",
            last_name="Petrov",
        )

        assert user.pk is not None
        assert user.password != "SecurePass1!"
        assert user.is_active is True

    def test_creates_user_with_patronymic(self):
        """Пользователь создаётся с отчеством."""
        user = create_user(
            email="pat@example.com",
            password="SecurePass1!",
            first_name="Ivan",
            last_name="Petrov",
            patronymic="Ivanovich",
        )

        assert user.patronymic == "Ivanovich"

    def test_raises_on_duplicate_email(self):
        """Повторная регистрация с тем же email невозможна."""
        create_user(
            email="dup@example.com",
            password="Pass1234!",
            first_name="A",
            last_name="B",
        )

        with pytest.raises(ValueError, match="already registered"):
            create_user(
                email="dup@example.com",
                password="Pass1234!",
                first_name="C",
                last_name="D",
            )


@pytest.mark.django_db
class TestAuthenticateUser:
    def test_returns_user_on_valid_credentials(self):
        """Возвращает пользователя при верных данных."""
        create_user(
            email="auth@example.com",
            password="MyPass99!",
            first_name="X",
            last_name="Y",
        )

        user = authenticate_user("auth@example.com", "MyPass99!")

        assert user is not None
        assert user.email == "auth@example.com"

    def test_returns_none_on_wrong_password(self):
        """Возвращает None при неверном пароле."""
        create_user(
            email="wrong@example.com",
            password="Correct1!",
            first_name="A",
            last_name="B",
        )

        result = authenticate_user("wrong@example.com", "WrongPass!")

        assert result is None

    def test_returns_none_for_unknown_email(self):
        """Возвращает None для несуществующего email."""
        result = authenticate_user("nobody@example.com", "Pass1234!")

        assert result is None

    def test_returns_none_for_inactive_user(self):
        """Неактивный пользователь не может войти."""
        user = create_user(
            email="inactive@example.com",
            password="Pass1234!",
            first_name="A",
            last_name="B",
        )
        user.is_active = False
        user.save()

        result = authenticate_user("inactive@example.com", "Pass1234!")

        assert result is None


@pytest.mark.django_db
class TestSoftDeleteUser:
    def test_sets_is_active_false(self):
        """Мягкое удаление устанавливает is_active=False."""
        user = create_user(
            email="del@example.com",
            password="Pass1234!",
            first_name="A",
            last_name="B",
        )

        soft_delete_user(user.pk)
        user.refresh_from_db()

        assert user.is_active is False

    def test_deleted_user_cannot_authenticate(self):
        """Удалённый пользователь не может войти."""
        user = create_user(
            email="delauth@example.com",
            password="Pass1234!",
            first_name="A",
            last_name="B",
        )
        soft_delete_user(user.pk)

        result = authenticate_user("delauth@example.com", "Pass1234!")

        assert result is None

    def test_record_remains_in_db_after_soft_delete(self):
        """Запись остаётся в БД после мягкого удаления."""
        from apps.users.models import User

        user = create_user(
            email="remain@example.com",
            password="Pass1234!",
            first_name="A",
            last_name="B",
        )
        soft_delete_user(user.pk)

        assert User.objects.filter(pk=user.pk).exists()
