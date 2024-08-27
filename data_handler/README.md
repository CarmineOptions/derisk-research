# DeRisk Data Handler

This project created to make data public for Derisk Alert app.
This app is not considering to you use in production. It's just a research project.

## Requirements
 - python3.11 
 - poetry
 - sqlalchemy

# Setup

### 1. Clone git repository

```bash
git clone https://github.com/CarmineOptions/derisk-research.git
```

### 2. Go to `data_handler/`


```bash
cd data_handler 
```

### 3. Set up `.env` file

Create `.env` file or just rename `.env.example` --> `.env`

```bash
mv .env.example .env
```

### 4. Provide all environment variables needed

```bash
DB_NAME=#
DB_USER=#
DB_PASSWORD=#
DB_HOST=db
DB_PORT=#
DERISK_API_URL=#
REDIS_HOST=redis
ERROR_CHAT_ID=# Actually your telegram id
```

### 5. Build your docker containers

```bash
docker-compose up -d --build
```

#### Stop your containers

```bash
docker-compose down
```

## Data migrations
In this project is using `alembic` for data migrations.
For generating new migration use this command:

```bash
alembic revision --autogenerate -m "your message"
```

After generating new migration, you need to apply it:

```bash
alembic upgrade head
```

For downgrading migration:

```bash
alembic downgrade -1
```

Useful commands:
Purge all celery tasks:
```bash
docker-compose run --rm celery celery -A celery_app.celery_conf purge
```
Purge all celery beat tasks:
```bash
docker-compose run --rm celery_beat celery -A celery_app.celery_conf purge
```
Go to bash
```bash
docker-compose exec backend bash
```