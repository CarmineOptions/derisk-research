FROM python:3.11

WORKDIR /code

COPY data_handler/poetry.lock data_handler/pyproject.toml /code/
COPY data_handler/entrypoint.sh /code/entrypoint.sh

RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev

# Adjust build context for folders out of Docker context
# Assuming data_handler and shared are located in the root directory, set the context to root
COPY shared /code/shared
COPY data_handler /code/data_handler

ENTRYPOINT ["bash", "/code/entrypoint.sh"]
