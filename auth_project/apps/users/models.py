from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
)
from django.db import models


class UserManager(BaseUserManager["User"]):
    def create_user(
        self,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        patronymic: str = "",
    ) -> "User":
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str,
        **extra: object,
    ) -> "User":
        user = self.create_user(
            email,
            password,
            **extra,  # type: ignore[arg-type]
        )
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """
    Кастомная модель пользователя.
    Идентификация по email.
    Soft delete через is_active=False.
    """

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    patronymic = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects: UserManager = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users"
        ordering = ("email",)

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        parts = [
            self.last_name,
            self.first_name,
            self.patronymic,
        ]
        return " ".join(p for p in parts if p)
