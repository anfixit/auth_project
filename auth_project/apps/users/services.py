"""Сервисный слой приложения users."""

__all__ = [
    'authenticate_user',
    'create_user',
    'get_role_names',
    'hash_password',
    'soft_delete_user',
    'verify_password',
]

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from apps.logger import get_logger
from apps.users.models import User

logger = get_logger(__name__)

_ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=2,
)


def hash_password(plain: str) -> str:
    """Хешировать пароль через Argon2id.

    Args:
        plain: Пароль в открытом виде.

    Returns:
        Хеш пароля в формате Argon2id.
    """
    return _ph.hash(plain)


def verify_password(hashed: str, plain: str) -> bool:
    """Проверить пароль против хеша.

    Args:
        hashed: Хеш пароля из базы данных.
        plain: Пароль в открытом виде для проверки.

    Returns:
        True если пароль совпадает, False иначе.
    """
    try:
        return _ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def create_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    patronymic: str = '',
) -> User:
    """Создать пользователя с хешированным паролем.

    Args:
        email: Адрес электронной почты.
        password: Пароль в открытом виде.
        first_name: Имя пользователя.
        last_name: Фамилия пользователя.
        patronymic: Отчество пользователя.

    Returns:
        Созданный экземпляр User.

    Raises:
        ValueError: Если email уже зарегистрирован.
    """
    if User.objects.filter(email=email).exists():
        logger.warning(
            'Попытка регистрации с уже занятым email: %s',
            email,
        )
        raise ValueError(f'Email {email!r} already registered.')
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        patronymic=patronymic,
    )
    user.password = hash_password(password)
    user.save()

    logger.info('Зарегистрирован новый пользователь: %s', email)
    return user


def authenticate_user(
    email: str,
    password: str,
) -> User | None:
    """Проверить email и пароль пользователя.

    Защита от timing-атак: холостой хеш выполняется
    даже при отсутствии пользователя в базе.

    Args:
        email: Адрес электронной почты.
        password: Пароль в открытом виде.

    Returns:
        Экземпляр User при успехе, None иначе.
    """
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        _ph.hash('dummy_to_prevent_timing_attack')
        logger.warning(
            'Неудачная попытка входа — пользователь не найден: %s',
            email,
        )
        return None

    if not verify_password(user.password, password):
        logger.warning(
            'Неудачная попытка входа — неверный пароль: %s',
            email,
        )
        return None

    logger.info('Успешный вход пользователя: %s', email)
    return user


def soft_delete_user(user_id: int) -> None:
    """Мягкое удаление пользователя.

    Устанавливает is_active=False. Запись остаётся
    в БД, логин становится невозможен.

    Args:
        user_id: Идентификатор пользователя.
    """
    User.objects.filter(pk=user_id).update(is_active=False)
    logger.info('Аккаунт деактивирован: user_id=%s', user_id)


def get_role_names(user_id: int) -> list[str]:
    """Получить список названий ролей пользователя.

    Args:
        user_id: Идентификатор пользователя.

    Returns:
        Список строк с названиями ролей.
    """
    # Отложенный импорт для разрыва циклической зависимости
    # users → access → users
    from apps.access.models import UserRole

    return list(
        UserRole.objects.filter(user_id=user_id)
        .select_related('role')
        .values_list('role__name', flat=True)
    )
