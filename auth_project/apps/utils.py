"""Общие утилиты проекта."""

__all__ = ['parse_json_body']

import json

from django.http import HttpRequest


def parse_json_body(request: HttpRequest) -> dict:
    """Безопасно распарсить JSON-тело запроса.

    Args:
        request: HTTP-запрос Django.

    Returns:
        Словарь с данными запроса или пустой словарь,
        если тело отсутствует или невалидно.
    """
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
