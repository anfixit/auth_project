from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class _Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    secret_key: SecretStr = Field(min_length=50)
    debug: bool = Field(default=False)
    allowed_hosts: str = Field(default="localhost,127.0.0.1")

    db_name: str = Field(default="auth_project")
    db_user: str = Field(default="postgres")
    db_password: SecretStr = Field(default="postgres")
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)

    jwt_access_token_expire_minutes: int = Field(default=15)
    jwt_refresh_token_expire_days: int = Field(default=7)


_s = _Settings()

SECRET_KEY = _s.secret_key.get_secret_value()
DEBUG = _s.debug
ALLOWED_HOSTS = _s.allowed_hosts.split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _s.db_name,
        "USER": _s.db_user,
        "PASSWORD": _s.db_password.get_secret_value(),
        "HOST": _s.db_host,
        "PORT": _s.db_port,
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "apps.users",
    "apps.auth_core",
    "apps.access",
    "apps.mock_views",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "apps.auth_core.middleware.JWTAuthMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "users.User"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
}

CACHES = {
    "default": {
        "BACKEND": ("django.core.cache.backends.locmem.LocMemCache"),
    }
}

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = _s.jwt_access_token_expire_minutes
JWT_REFRESH_TOKEN_EXPIRE_DAYS = _s.jwt_refresh_token_expire_days
