import pytest
from django.test import RequestFactory

from apps.access.models import AccessRule, BusinessElement, Role, UserRole
from apps.users.models import User
from apps.users.services import hash_password


@pytest.fixture
def factory() -> RequestFactory:
    """Фабрика HTTP-запросов для тестов."""
    return RequestFactory()


@pytest.fixture
def role_admin(db) -> Role:
    """Создать роль admin."""
    return Role.objects.create(
        name='admin',
        description='Admin role',
    )


@pytest.fixture
def role_user(db) -> Role:
    """Создать роль user."""
    return Role.objects.create(
        name='user',
        description='Regular user',
    )


@pytest.fixture
def element_products(db) -> BusinessElement:
    """Создать бизнес-объект products."""
    return BusinessElement.objects.create(name='products')


@pytest.fixture
def element_access_rules(db) -> BusinessElement:
    """Создать бизнес-объект access_rules."""
    return BusinessElement.objects.create(name='access_rules')


@pytest.fixture
def admin_user(db, role_admin: Role) -> User:
    """Создать пользователя с ролью admin."""
    user = User.objects.create(
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        password=hash_password('AdminPass1!'),
    )
    UserRole.objects.create(user=user, role=role_admin)
    return user


@pytest.fixture
def regular_user(db, role_user: Role) -> User:
    """Создать пользователя с ролью user."""
    user = User.objects.create(
        email='user@example.com',
        first_name='Regular',
        last_name='User',
        password=hash_password('UserPass1!'),
    )
    UserRole.objects.create(user=user, role=role_user)
    return user


@pytest.fixture
def admin_rule(
    db,
    role_admin: Role,
    element_products: BusinessElement,
) -> AccessRule:
    """Дать роли admin полный доступ к products."""
    return AccessRule.objects.create(
        role=role_admin,
        element=element_products,
        read=True,
        read_all=True,
        create=True,
        update=True,
        update_all=True,
        delete=True,
        delete_all=True,
    )
