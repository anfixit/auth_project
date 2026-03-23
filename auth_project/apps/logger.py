"""Настройка логирования для проекта."""

__all__ = ['get_logger']

import logging
import sys
from pathlib import Path

_LOG_FORMAT = (
    '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s'
)
_LOG_DIR = Path(__file__).resolve().parent.parent / 'logs'


def get_logger(name: str) -> logging.Logger:
    """Создать и настроить логгер с выводом в файл и консоль.

    Повторный вызов с тем же именем вернёт уже
    настроенный логгер без дублирования handlers.

    Args:
        name: Имя логгера, обычно __name__ модуля.

    Returns:
        Настроенный экземпляр logging.Logger.
    """
    _LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(_LOG_FORMAT))

    file_handler = logging.FileHandler(
        _LOG_DIR / f'{name}.log',
        encoding='utf-8',
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))

    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger
