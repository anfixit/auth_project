"""Декораторы проверки аутентификации и прав доступа."""

__all__ = ['has_permission', 'login_required']

from collections.abc import Callable
from functools import wraps
from typing import Any

from django.http import HttpRequest, JsonResponse

from apps.access.services import check_permission


def login_required(
    view: Callable[..., Any],
) -> Callable[..., Any]:
    """Декоратор: возвращает 401 если пользователь не идентифицирован.

    Args:
        view: Декорируемая view-функция.

    Returns:
        Обёрнутая функция с проверкой аутентификации.
    """

    @wraps(view)
    def wrapper(
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if not getattr(request, 'user_id', None):
            return JsonResponse(
                {'detail': 'Authentication required.'},
                status=401,
            )
        return view(request, *args, **kwargs)

    return wrapper


def has_permission(
    element: str,
    action: str,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Фабрика декораторов: проверяет право action на объект element.

    Использование:
        @has_permission('products', 'read_all')
        def my_view(request): ...

    Args:
        element: Название бизнес-объекта, например 'products'.
        action: Название права, например 'read_all'.

    Returns:
        Декоратор, возвращающий 401 или 403 при отсутствии доступа.
    """

    def decorator(
        view: Callable[..., Any],
    ) -> Callable[..., Any]:

        @wraps(view)
        def wrapper(
            request: HttpRequest,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            user_id = getattr(request, 'user_id', None)
            if not user_id:
                return JsonResponse(
                    {'detail': 'Authentication required.'},
                    status=401,
                )

            roles: list[str] = getattr(request, 'roles', [])
            if not check_permission(roles, element, action):
                return JsonResponse(
                    {'detail': 'Forbidden.'},
                    status=403,
                )

            return view(request, *args, **kwargs)

        return wrapper

    return decorator
