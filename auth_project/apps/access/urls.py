from django.urls import path

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

urlpatterns = [
    # Roles
    path('roles/', roles_list_view, name='roles-list'),
    path(
        'roles/create/',
        roles_create_view,
        name='roles-create',
    ),
    path(
        'roles/<int:role_id>/delete/',
        roles_delete_view,
        name='roles-delete',
    ),
    # Business Elements
    path(
        'elements/',
        elements_list_view,
        name='elements-list',
    ),
    # Access Rules
    path('rules/', rules_list_view, name='rules-list'),
    path(
        'rules/create/',
        rules_create_view,
        name='rules-create',
    ),
    path(
        'rules/<int:rule_id>/update/',
        rules_update_view,
        name='rules-update',
    ),
    path(
        'rules/<int:rule_id>/delete/',
        rules_delete_view,
        name='rules-delete',
    ),
    # User ↔ Role assignments
    path(
        'user-roles/',
        user_roles_list_view,
        name='user-roles-list',
    ),
    path(
        'user-roles/assign/',
        user_roles_assign_view,
        name='user-roles-assign',
    ),
    path(
        'user-roles/<int:user_role_id>/remove/',
        user_roles_remove_view,
        name='user-roles-remove',
    ),
]
