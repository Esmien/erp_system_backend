FROM python:3.12-slim

WORKDIR /app


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Устанавливаем системные зависимости (нужны для сборки bcrypt, asyncpg и т.д.) и сам Poetry
RUN apt-get update && apt-get install -y gcc libffi-dev \
    && pip install --no-cache-dir poetry \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Сначала копируем только файлы зависимостей (для кэширования слоя Docker)
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости (без тестов и линтеров из dev-группы)
RUN poetry install --without dev --no-interaction --no-ansi --no-root

# Копируем остальной код проекта
COPY . .

# Запускаем Uvicorn
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]