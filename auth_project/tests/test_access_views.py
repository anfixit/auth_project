"""Тесты для apps/access/views.py."""

import json

import pytest
from django.test import RequestFactory

from apps.access.models import AccessRule, BusinessElement, Role, UserRole
from apps.access.views import (
    elements_list_view,
    roles_create_view,
    roles_delete_view,
    roles_list_view,
    rules_create_view,
    rules_delete_view,
    rules_list_view,
    rules_update_view,
    user_roles_assign_view,
    user_roles_list_view,
    user_roles_remove_view,
)
from apps.users.models import User
from apps.users.services import create_user, hash_password


@pytest.fixture
def factory() -> RequestFactory:
    """Фабрика HTTP-запросов."""
    return RequestFactory()


@pytest.fixture
def admin_setup(db):
    """Создать пользователя admin с полными правами на access_rules и users."""
    user = User.objects.create(
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        password=hash_password('AdminPass1!'),
    )
    role = Role.objects.create(name='admin')
    UserRole.objects.create(user=user, role=role)

    for element_name in ('access_rules', 'users'):
        element = BusinessElement.objects.create(name=element_name)
        AccessRule.objects.create(
            role=role,
            element=element,
            read=True,
            read_all=True,
            create=True,
            update=True,
            update_all=True,
            delete=True,
            delete_all=True,
        )
    return user, role


def _req(factory, method, url, data=None, user_id=None, roles=None):
    """Вспомогательная функция создания запроса."""
    kwargs = {'content_type': 'application/json'}
    if data is not None:
        kwargs['data'] = json.dumps(data)
    request = getattr(factory, method)(url, **kwargs)
    request.user_id = user_id
    request.roles = roles or []
    return request


@pytest.mark.django_db
class TestRolesListView:
    def test_returns_roles_list(self, factory, admin_setup):
        """Возвращает список ролей."""
        user, role = admin_setup
        request = _req(
            factory,
            'get',
            '/api/v1/access/roles/',
            user_id=user.pk,
            roles=['admin'],
        )

        response = roles_list_view(request)
        data = json.loads(response.content)

        assert response.status_code == 200
        assert isinstance(data, list)
        assert any(r['name'] == 'admin' for r in data)

    def test_returns_401_if_not_authenticated(self, factory, db):
        """Возвращает 401 если не авторизован."""
        request = _req(
            factory,
            'get',
            '/api/v1/access/roles/',
            user_id=None,
        )

        response = roles_list_view(request)

        assert response.status_code == 401

    def test_returns_403_without_permission(self, factory, db):
        """Возвращает 403 если нет права read_all."""
        role = Role.objects.create(name='guest')
        element = BusinessElement.objects.create(name='access_rules')
        AccessRule.objects.create(
            role=role,
            element=element,
            read_all=False,
        )
        request = _req(
            factory,
            'get',
            '/api/v1/access/roles/',
            user_id=1,
            roles=['guest'],
        )

        response = roles_list_view(request)

        assert response.status_code == 403


@pytest.mark.django_db
class TestRolesCreateView:
    def test_creates_role(self, factory, admin_setup):
        """Создаёт новую роль."""
        user, role = admin_setup
        request = _req(
            factory,
            'post',
            '/api/v1/access/roles/create/',
            data={'name': 'moderator', 'description': 'Mod'},
            user_id=user.pk,
            roles=['admin'],
        )

        response = roles_create_view(request)
        data = json.loads(response.content)

        assert response.status_code == 201
        assert data['name'] == 'moderator'

    def test_returns_400_on_duplicate_name(
        self,
        factory,
        admin_setup,
    ):
        """Возвращает 400 при дублировании имени роли."""
        user, role = admin_setup
        request = _req(
            factory,
            'post',
            '/api/v1/access/roles/create/',
            data={'name': 'admin'},
            user_id=user.pk,
            roles=['admin'],
        )

        response = roles_create_view(request)

        assert response.status_code == 400

    def test_returns_401_if_not_authenticated(self, factory, db):
        """Возвращает 401 если не авторизован."""
        request = _req(
            factory,
            'post',
            '/api/v1/access/roles/create/',
            data={'name': 'new'},
            user_id=None,
        )

        response = roles_create_view(request)

        assert response.status_code == 401


@pytest.mark.django_db
class TestRolesDeleteView:
    def test_deletes_role(self, factory, admin_setup):
        """Удаляет роль по id."""
        user, role = admin_setup
        new_role = Role.objects.create(name='to_delete')

        request = _req(
            factory,
            'delete',
            f'/api/v1/access/roles/{new_role.pk}/delete/',
            user_id=user.pk,
            roles=['admin'],
        )

        response = roles_delete_view(request, role_id=new_role.pk)

        assert response.status_code == 200
        assert not Role.objects.filter(pk=new_role.pk).exists()

    def test_returns_404_if_not_found(self, factory, admin_setup):
        """Возвращает 404 если роль не найдена."""
        user, role = admin_setup
        request = _req(
            factory,
            'delete',
            '/api/v1/access/roles/99999/delete/',
            user_id=user.pk,
            roles=['admin'],
        )

        response = roles_delete_view(request, role_id=99999)

        assert response.status_code == 404


@pytest.mark.django_db
class TestElementsListView:
    def test_returns_elements_list(self, factory, admin_setup):
        """Возвращает список бизнес-объектов."""
        user, role = admin_setup
        request = _req(
            factory,
            'get',
            '/api/v1/access/elements/',
            user_id=user.pk,
            roles=['admin'],
        )

        response = elements_list_view(request)
        data = json.loads(response.content)

        assert response.status_code == 200
        assert isinstance(data, list)
        assert len(data) >= 2


@pytest.mark.django_db
class TestRulesViews:
    def test_list_returns_matrix(self, factory, admin_setup):
        """Возвращает матрицу прав."""
        user, role = admin_setup
        request = _req(
            factory,
            'get',
            '/api/v1/access/rules/',
            user_id=user.pk,
            roles=['admin'],
        )

        response = rules_list_view(request)
        data = json.loads(response.content)

        assert response.status_code == 200
        assert isinstance(data, list)

    def test_create_rule(self, factory, admin_setup):
        """Создаёт правило доступа."""
        user, role = admin_setup
        new_role = Role.objects.create(name='tester')
        element = BusinessElement.objects.get(name='access_rules')

        request = _req(
            factory,
            'post',
            '/api/v1/access/rules/create/',
            data={
                'role': new_role.pk,
                'element': element.pk,
                'read': True,
                'read_all': False,
                'create': False,
                'update': False,
                'update_all': False,
                'delete': False,
                'delete_all': False,
            },
            user_id=user.pk,
            roles=['admin'],
        )

        response = rules_create_view(request)

        assert response.status_code == 201

    def test_update_rule(self, factory, admin_setup):
        """Обновляет правило доступа."""
        user, role = admin_setup
        element = BusinessElement.objects.get(name='access_rules')
        new_role = Role.objects.create(name='tester2')
        rule = AccessRule.objects.create(
            role=new_role,
            element=element,
            read=False,
        )

        request = _req(
            factory,
            'patch',
            f'/api/v1/access/rules/{rule.pk}/update/',
            data={'read': True},
            user_id=user.pk,
            roles=['admin'],
        )

        response = rules_update_view(request, rule_id=rule.pk)
        data = json.loads(response.content)

        assert response.status_code == 200
        assert data['read'] is True

    def test_delete_rule(self, factory, admin_setup):
        """Удаляет правило доступа."""
        user, role = admin_setup
        element = BusinessElement.objects.get(name='access_rules')
        new_role = Role.objects.create(name='tester3')
        rule = AccessRule.objects.create(
            role=new_role,
            element=element,
        )

        request = _req(
            factory,
            'delete',
            f'/api/v1/access/rules/{rule.pk}/delete/',
            user_id=user.pk,
            roles=['admin'],
        )

        response = rules_delete_view(request, rule_id=rule.pk)

        assert response.status_code == 200
        assert not AccessRule.objects.filter(pk=rule.pk).exists()

    def test_update_returns_404(self, factory, admin_setup):
        """Возвращает 404 если правило не найдено."""
        user, role = admin_setup
        request = _req(
            factory,
            'patch',
            '/api/v1/access/rules/99999/update/',
            data={'read': True},
            user_id=user.pk,
            roles=['admin'],
        )

        response = rules_update_view(request, rule_id=99999)

        assert response.status_code == 404

    def test_delete_returns_404(self, factory, admin_setup):
        """Возвращает 404 если правило не найдено."""
        user, role = admin_setup
        request = _req(
            factory,
            'delete',
            '/api/v1/access/rules/99999/delete/',
            user_id=user.pk,
            roles=['admin'],
        )

        response = rules_delete_view(request, rule_id=99999)

        assert response.status_code == 404


@pytest.mark.django_db
class TestUserRolesViews:
    def test_list_user_roles(self, factory, admin_setup):
        """Возвращает список назначений ролей."""
        user, role = admin_setup
        request = _req(
            factory,
            'get',
            '/api/v1/access/user-roles/',
            user_id=user.pk,
            roles=['admin'],
        )

        response = user_roles_list_view(request)
        data = json.loads(response.content)

        assert response.status_code == 200
        assert isinstance(data, list)

    def test_assign_role_to_user(self, factory, admin_setup):
        """Назначает роль пользователю."""
        user, role = admin_setup
        new_role = Role.objects.create(name='operator')
        new_user = User.objects.create(
            email='op@example.com',
            first_name='Op',
            last_name='User',
            password=hash_password('OpPass1!'),
        )

        request = _req(
            factory,
            'post',
            '/api/v1/access/user-roles/assign/',
            data={'user': new_user.pk, 'role': new_role.pk},
            user_id=user.pk,
            roles=['admin'],
        )

        response = user_roles_assign_view(request)

        assert response.status_code == 201
        assert UserRole.objects.filter(
            user=new_user,
            role=new_role,
        ).exists()

    def test_assign_idempotent(self, factory, admin_setup):
        """Повторное назначение той же роли возвращает 200."""
        admin, role = admin_setup
        # создаём нового пользователя без роли
        other = create_user(
            email='idempotent@example.com',
            password='Pass1234!',
            first_name='A',
            last_name='B',
        )
        # первый раз — 201
        for _ in range(2):
            request = _req(
                factory,
                'post',
                '/api/v1/access/user-roles/assign/',
                data={'user': other.pk, 'role': role.pk},
                user_id=admin.pk,
                roles=['admin'],
            )
            response = user_roles_assign_view(request)

        # второй раз — 200 (уже существует)
        assert response.status_code == 200

    def test_remove_user_role(self, factory, admin_setup):
        """Снимает роль с пользователя."""
        user, role = admin_setup
        new_role = Role.objects.create(name='temp')
        user_role = UserRole.objects.create(user=user, role=new_role)

        request = _req(
            factory,
            'delete',
            f'/api/v1/access/user-roles/{user_role.pk}/remove/',
            user_id=user.pk,
            roles=['admin'],
        )

        response = user_roles_remove_view(
            request,
            user_role_id=user_role.pk,
        )

        assert response.status_code == 200
        assert not UserRole.objects.filter(pk=user_role.pk).exists()

    def test_remove_returns_404(self, factory, admin_setup):
        """Возвращает 404 если назначение не найдено."""
        user, role = admin_setup
        request = _req(
            factory,
            'delete',
            '/api/v1/access/user-roles/99999/remove/',
            user_id=user.pk,
            roles=['admin'],
        )

        response = user_roles_remove_view(
            request,
            user_role_id=99999,
        )

        assert response.status_code == 404
