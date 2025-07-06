FROM python:3.11

WORKDIR /app

COPY data_handler/poetry.lock data_handler/pyproject.toml .

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/usr/local/ POETRY_VERSION=1.8.3 python3 -\
    && poetry config virtualenvs.create false \
    && poetry install --no-dev

# Adjust build context for folders out of Docker context
# Assuming data_handler and shared are located in the root directory, set the context to root
COPY shared shared/
COPY data_handler data_handler/

ENTRYPOINT ["bash", "/app/data_handler/entrypoint.sh"]
