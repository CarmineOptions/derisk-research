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
