from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from apps.users.models import User

_ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=2,
)


def hash_password(plain: str) -> str:
    """Хешировать пароль через Argon2id."""
    return _ph.hash(plain)


def verify_password(hashed: str, plain: str) -> bool:
    """Проверить пароль. False при несовпадении."""
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def create_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    patronymic: str = "",
) -> User:
    """
    Создать пользователя с хешированным паролем.

    Raises:
        ValueError: email уже занят.
    """
    if User.objects.filter(email=email).exists():
        raise ValueError(f"Email {email!r} already registered.")
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        patronymic=patronymic,
    )
    user.password = hash_password(password)
    user.save()
    return user


def authenticate_user(
    email: str,
    password: str,
) -> User | None:
    """
    Проверить email + пароль.

    Защита от timing attack: холостой хеш
    при отсутствии пользователя.
    """
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        _ph.hash("dummy_to_prevent_timing_attack")
        return None

    if not verify_password(user.password, password):
        return None

    return user


def soft_delete_user(user_id: int) -> None:
    """
    Мягкое удаление: is_active=False.
    Запись остаётся в БД, логин невозможен.
    """
    User.objects.filter(pk=user_id).update(is_active=False)


def get_role_names(user_id: int) -> list[str]:
    """Получить список названий ролей пользователя."""
    from apps.access.models import UserRole

    return list(
        UserRole.objects.filter(user_id=user_id)
        .select_related("role")
        .values_list("role__name", flat=True)
    )
