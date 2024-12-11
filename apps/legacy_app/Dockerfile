FROM python:3.10

WORKDIR /app

RUN pip install poetry
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY src src
COPY app.py .
COPY update_data.py .

CMD ["streamlit", "run", "app.py"]
