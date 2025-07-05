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
RUN pip install poetry

COPY apps/dashboard_app/pyproject.toml apps/dashboard_app/poetry.lock* ./dashboard_app/
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-root

COPY apps/shared/pyproject.toml apps/shared/poetry.lock* ./shared/
RUN poetry install --no-interaction --no-root 

COPY apps/dashboard_app/alembic ./dashboard_app/alembic
COPY apps/dashboard_app/app/ ./dashboard_app/app/
COPY apps/shared/ ./shared/
COPY apps/data_handler/ ./data_handler/

EXPOSE 8000

ENTRYPOINT ["uvicorn", "dashboard_app.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
