"""Сериализаторы приложения access."""

__all__ = [
    'AccessRuleSerializer',
    'BusinessElementSerializer',
    'RoleSerializer',
    'UserRoleSerializer',
]

from rest_framework import serializers

from apps.access.models import AccessRule, BusinessElement, Role, UserRole


class RoleSerializer(serializers.ModelSerializer):
    """Сериализатор роли пользователя."""

    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'created_at')
        read_only_fields = ('id', 'created_at')


class BusinessElementSerializer(serializers.ModelSerializer):
    """Сериализатор бизнес-объекта."""

    class Meta:
        model = BusinessElement
        fields = ('id', 'name', 'description')
        read_only_fields = ('id',)


class AccessRuleSerializer(serializers.ModelSerializer):
    """Сериализатор правила доступа роли к объекту."""

    role_name = serializers.CharField(
        source='role.name',
        read_only=True,
    )
    element_name = serializers.CharField(
        source='element.name',
        read_only=True,
    )

    class Meta:
        model = AccessRule
        fields = (
            'id',
            'role',
            'role_name',
            'element',
            'element_name',
            'read',
            'read_all',
            'create',
            'update',
            'update_all',
            'delete',
            'delete_all',
        )
        read_only_fields = ('id', 'role_name', 'element_name')


class UserRoleSerializer(serializers.ModelSerializer):
    """Сериализатор назначения роли пользователю."""

    role_name = serializers.CharField(
        source='role.name',
        read_only=True,
    )
    user_email = serializers.CharField(
        source='user.email',
        read_only=True,
    )

    class Meta:
        model = UserRole
        fields = (
            'id',
            'user',
            'user_email',
            'role',
            'role_name',
            'assigned_at',
        )
        read_only_fields = (
            'id',
            'role_name',
            'user_email',
            'assigned_at',
        )
