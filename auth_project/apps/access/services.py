from django.core.cache import cache

from apps.access.models import AccessRule

_CACHE_TTL = 300  # 5 минут


def check_permission(
    role_names: list[str],
    element_name: str,
    action: str,
) -> bool:
    """Проверить право доступа роли на бизнес-объект.

    Результат кешируется на 5 минут — права меняются редко.
    Возвращает True если хотя бы одна роль из списка
    имеет право action на элемент element_name.

    Args:
        role_names: список названий ролей пользователя.
        element_name: название бизнес-объекта,
            например 'products'.
        action: название права,
            например 'read_all' или 'create'.

    Returns:
        True если доступ разрешён, False иначе.
    """
    if not role_names:
        return False

    cache_key = f"perm:{':'.join(sorted(role_names))}:{element_name}:{action}"
    cached = cache.get(cache_key)
    if cached is not None:
        return bool(cached)

    rules = AccessRule.objects.filter(
        role__name__in=role_names,
        element__name=element_name,
    ).values(action)

    result = any(rule.get(action, False) for rule in rules)

    cache.set(cache_key, result, _CACHE_TTL)
    return result


def invalidate_permission_cache() -> None:
    """Сбросить весь кеш прав.

    Вызывать при любом изменении AccessRule,
    чтобы новые права вступили в силу немедленно.
    """
    cache.clear()
