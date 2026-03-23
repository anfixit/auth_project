FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Не запускаем от root
RUN useradd -m appuser
WORKDIR /app

# Устанавливаем uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Зависимости отдельным слоем для кеша
COPY pyproject.toml .
RUN uv sync --no-dev

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
