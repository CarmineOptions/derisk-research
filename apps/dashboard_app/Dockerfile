FROM python:3.12

ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH="/app"

RUN apt-get update && apt-get install -y \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install poetry

COPY dashboard_app/pyproject.toml dashboard_app/poetry.lock* ./dashboard_app/
COPY shared/pyproject.toml shared/poetry.lock* ./shared/

WORKDIR /app/dashboard_app
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-root
WORKDIR /app/shared
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-root
WORKDIR /app

COPY dashboard_app/entrypoint.sh ./dashboard_app/
RUN chmod +x ./dashboard_app/entrypoint.sh

# CORRECTED: Point to the script's actual location.
ENTRYPOINT ["bash" , "./dashboard_app/entrypoint.sh"]