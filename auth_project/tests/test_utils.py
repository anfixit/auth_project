"""Тесты для apps/utils.py."""

import json

import pytest
from django.test import RequestFactory

from apps.utils import parse_json_body


@pytest.fixture
def factory() -> RequestFactory:
    """Фабрика HTTP-запросов."""
    return RequestFactory()


class TestParseJsonBody:
    def test_returns_dict_on_valid_json(self, factory):
        """Возвращает словарь при валидном JSON."""
        request = factory.post(
            '/',
            data=json.dumps({'key': 'value'}),
            content_type='application/json',
        )

        result = parse_json_body(request)

        assert result == {'key': 'value'}

    def test_returns_empty_dict_on_empty_body(self, factory):
        """Возвращает пустой словарь при пустом теле."""
        request = factory.post(
            '/',
            data='',
            content_type='application/json',
        )

        result = parse_json_body(request)

        assert result == {}

    def test_returns_empty_dict_on_invalid_json(self, factory):
        """Возвращает пустой словарь при невалидном JSON."""
        request = factory.post(
            '/',
            data='not a json',
            content_type='application/json',
        )

        result = parse_json_body(request)

        assert result == {}

    def test_returns_empty_dict_on_malformed_json(self, factory):
        """Возвращает пустой словарь при сломанном JSON."""
        request = factory.post(
            '/',
            data='{key: value}',
            content_type='application/json',
        )

        result = parse_json_body(request)

        assert result == {}

    def test_parses_nested_json(self, factory):
        """Корректно парсит вложенный JSON."""
        payload = {'user': {'email': 'test@example.com', 'age': 25}}
        request = factory.post(
            '/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        result = parse_json_body(request)

        assert result == payload

    def test_parses_list_in_json(self, factory):
        """Корректно парсит JSON со списком."""
        payload = {'roles': ['admin', 'user']}
        request = factory.post(
            '/',
            data=json.dumps(payload),
            content_type='application/json',
        )

        result = parse_json_body(request)

        assert result['roles'] == ['admin', 'user']
