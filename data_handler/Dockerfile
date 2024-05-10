FROM python:3.11

WORKDIR /code

COPY poetry.lock pyproject.toml /code/

RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev

COPY . /code/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
