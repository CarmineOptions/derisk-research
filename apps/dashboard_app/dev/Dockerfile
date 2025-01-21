FROM python:3.10

WORKDIR /app

RUN pip install poetry
COPY dashboard_app/pyproject.toml dashboard_app/poetry.lock* ./
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --no-root

RUN touch ./__init__.py
COPY dashboard_app/ .
COPY data_handler/ ./data_handler/
COPY shared/ ./shared/

CMD ["streamlit", "run", "dashboard.py"]
