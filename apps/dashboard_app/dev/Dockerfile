FROM python:3.10

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install poetry
COPY dashboard_app/pyproject.toml dashboard_app/poetry.lock* ./
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --no-root

RUN touch ./__init__.py
COPY dashboard_app/ .
COPY data_handler/ ./data_handler/
COPY shared/ ./shared/
ENTRYPOINT ["../.entrypoint.sh"]

# Copy the requirements file and install Python dependencies