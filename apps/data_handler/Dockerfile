FROM python:3.11

WORKDIR /code

COPY poetry.lock pyproject.toml /code/

RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev

# Adjust build context for folders out of Docker context
# Assuming data_handler and shared are located in the root directory, set the context to root
COPY data_handler /code/data_handler
COPY shared /code/shared

ENTRYPOINT ["bash", "/app/entrypoint.sh"]
