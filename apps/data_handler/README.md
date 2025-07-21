# DeRisk Data Handler

## Overview
Data processing and analysis component: Collects data from DeFi, analyzes it, and saves it to the db. It contains Celery tasks to schedule data collection runs. Once the data is collected, it triggers an endpoint on the `dashboard_app`



## Setup
1. To set up this project run next command for local development in `derisk-research` directory:

2. Environment Configuration:
```bash
cp apps/data_handler/.env.dev apps/data_handler/.env
```
3. Start the Services:

```bash
docker compose -f devops/dev/docker-compose.data-handler.yaml up --build
```
4. Stop the Services:
```bash
docker compose -f devops/dev/docker-compose.data-handler.yaml down
```

5. To run test cases for this project run next command in `derisk-research` directory:
```bash
make test_data_handler
```

## Data migrations with Alembic
In this project is using alembic for data migrations.

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
docker compose run --rm celery celery -A celery_conf purge
```
Purge all celery beat tasks:
```bash
docker compose run --rm celery_beat celery -A celery_conf purge
```
Go to bash
```bash
docker compose exec backend bash
```


## How to run migration command:
1. Set up `.env.dev` into `derisk-research/apps/data_handler`
2. Go back to `derisk-research/apps` directory
3. Then run bash script to migrate:
```bash
bash data_handler/migrate.sh
```