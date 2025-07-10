FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH="/app:/app/dashboard_app"

WORKDIR /app

RUN pip install poetry

COPY dashboard_app/app/telegram_app/pyproject.toml dashboard_app/app/telegram_app/poetry.lock* ./

RUN poetry config virtualenvs.create false && poetry install --only main --no-root

COPY dashboard_app/ /app/dashboard_app/
COPY shared/ ./shared/

CMD ["poetry", "run", "python", "-m", "dashboard_app.app.telegram_app.telegram"]