FROM python:3.12

ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH="/app"


RUN apt-get update && apt-get install -y \
  postgresql-client \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install poetry
COPY dashboard_app/pyproject.toml dashboard_app/poetry.lock* ./
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-root 

COPY shared/pyproject.toml shared/poetry.lock* ./
RUN poetry install --no-interaction --no-root 


COPY dashboard_app/ ./dashboard_app/
COPY shared/ ./shared/
RUN touch ./dashboard_app/__init__.py
RUN touch ./__init__.py
COPY dashboard_app/entrypoint.sh ./
COPY dashboard_app/derisk_dump_part_aa.sql ./

ENTRYPOINT ["bash" , "entrypoint.sh"]
