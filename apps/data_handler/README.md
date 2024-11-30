# DeRisk Data Handler

## Overview
This project was created to make data public for Derisk Alert app.
This app is not intended for you to use in production. It's just a research project.

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

### 3. Configure Environment Variables

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
TELEGRAM_TOKEN=#
```

### 5. Build your docker containers

```bash
docker-compose up -d --build
```

#### Stop your containers

```bash
docker-compose down
```

## Data migrations with Alembic
In this project is using `alembic` for data migrations.

### Generating Migrations
Navigate to the `apps` folder and generate a new migration using the following command:
```bash
cd apps
alembic -c data_handler/alembic.ini revision --autogenerate -m "your message"
```
### Applying Migrations
After generating new migration, you need to apply it:

```bash
alembic -c data_handler/alembic.ini upgrade head
```
### Rolling Back Migrations
For downgrading migration:

```bash
alembic -c data_handler/alembic.ini downgrade -1
```

### Migration Utility Commands
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


## How to run migration command:
1. Set up `.env.dev` into `derisk-research/apps/data_handler`
2. Go back to `derisk-research/apps` directory
3. Then run bash script to migrate:
```bash
bash data_handler/migrate.sh
```
