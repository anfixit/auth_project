"""Модели приложения access."""

__all__ = ["AccessRule", "BusinessElement", "Role", "UserRole"]

from django.db import models

from apps.users.models import User


class Role(models.Model):
    """Роль пользователя в системе.

    Примеры: admin, manager, user, guest.
    """

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "roles"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class UserRole(models.Model):
    """Связь пользователь ↔ роль.

    У одного пользователя может быть несколько ролей.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_roles",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_roles"
        unique_together = ("user", "role")

    def __str__(self) -> str:
        return f"{self.user.email} → {self.role.name}"


class BusinessElement(models.Model):
    """Бизнес-объект приложения, к которому применяются права.

    Примеры: users, products, shops, orders, access_rules.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "business_elements"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class AccessRule(models.Model):
    """Матрица прав: роль × бизнес-объект × действия.

    Семантика полей:
    - read        — читать свои объекты (owner_id == user.id)
    - read_all    — читать все объекты
    - create      — создавать объекты
    - update      — редактировать свои объекты
    - update_all  — редактировать все объекты
    - delete      — удалять свои объекты
    - delete_all  — удалять все объекты
    """

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="access_rules",
    )
    element = models.ForeignKey(
        BusinessElement,
        on_delete=models.CASCADE,
        related_name="access_rules",
    )

    read = models.BooleanField(default=False)
    read_all = models.BooleanField(default=False)
    create = models.BooleanField(default=False)
    update = models.BooleanField(default=False)
    update_all = models.BooleanField(default=False)
    delete = models.BooleanField(default=False)
    delete_all = models.BooleanField(default=False)

    class Meta:
        db_table = "access_rules"
        unique_together = ("role", "element")

    def __str__(self) -> str:
        return f"{self.role.name} → {self.element.name}"
