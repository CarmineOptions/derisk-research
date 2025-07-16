FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir /app
WORKDIR /app

ENV PYTHONPATH "${PYTHONPATH}:/app"

COPY web_app/pyproject.toml /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY . /app

ENTRYPOINT ["bash", "/app/entrypoint.sh"]

# Expose the port
EXPOSE 8000
