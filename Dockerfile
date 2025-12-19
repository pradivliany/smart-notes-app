FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install --upgrade pip
RUN pip install poetry
RUN poetry install --only main --no-root --no-interaction

COPY . /app

EXPOSE 8000

CMD ["poetry", "run", "gunicorn", "notes.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
