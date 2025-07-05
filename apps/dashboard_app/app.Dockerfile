FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH="/app"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libpq-dev gcc g++ make libffi-dev build-essential \
       curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install poetry

COPY dashboard_app/pyproject.toml dashboard_app/poetry.lock* ./dashboard_app/
COPY shared/pyproject.toml shared/poetry.lock* ./shared/

# Install dependencies for dashboard_app
WORKDIR /app/dashboard_app
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-root

# Install dependencies for shared
WORKDIR /app/shared
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-root

WORKDIR /app

EXPOSE 8000

ENTRYPOINT ["uvicorn", "dashboard_app.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]