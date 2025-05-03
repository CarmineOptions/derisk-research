FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

ENV PATH "/root/.local/bin:$PATH"
ENV PYTHONPATH="/app"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libpq-dev gcc g++ make libffi-dev build-essential \
       curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY dashboard_app/pyproject.toml dashboard_app/poetry.lock* ./
RUN pip install poetry
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-root

COPY dashboard_app/alembic ./alembic
COPY dashboard_app/app/ ./app/
COPY dashboard_app/app/ ./app/
COPY shared/ ./shared/
COPY data_handler/ ./data_handler/

EXPOSE 8000

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
