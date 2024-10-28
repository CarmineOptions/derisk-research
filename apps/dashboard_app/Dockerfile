FROM python:3.10

WORKDIR /app

RUN pip install poetry
COPY legacy_app/pyproject.toml legacy_app/poetry.lock* ./
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY legacy_app/src legacy_app/src
COPY legacy_app/app.py .
COPY legacy_app/update_data.py .

CMD ["streamlit", "run", "app.py"]

