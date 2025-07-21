# DeRisk Dashboard App
Interactive dashboard application for visualizing and analyzing DeRisk data.
Works as a server for the [`frontend_dashboard`](./apps/frontend_dashboard/README.md). Generates an analytics dashboard using Streamlit. Contains an API to handle the Telegram webhook and send bot messages.
Key Features:
- Interactive data visualization
- Protocol statistics monitoring
- Loan portfolio analysis
- Real-time data updates



## Setup
1. To set up this project run next command for local development in `derisk-research` directory:

2. Environment Configuration:
```bash
cp apps/dashboard_app/.env.dev apps/dashboard_app/.env
```
3. Start the Services:

```bash
docker-compose -f devops/dev/docker-compose.dashboard-app.yaml up --build
```
4. Stop the Services:
```bash
docker-compose -f devops/dev/docker-compose.dashboard-app.yaml down
```


### Adding New Charts

1. Create chart module in `charts/`
2. Implement chart logic using main.py templates
3. Register in dashboard.py

### Data Integration

Use `data_connector.py` to add new data sources:

```python
from data_connector import DataConnector

connector = DataConnector()
data = connector.get_data()
```

## Database Migrations

This project uses Alembic for database migrations.

### Database Configuration

Database connection settings are loaded from environment variables. Make sure the following variables are set:

- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `DB_NAME`: Database name

You can set these variables in a `.env` file in the project root directory.

### Apply Migrations

To apply all pending migrations:

```bash
poetry run alembic upgrade head
```

To apply migrations up to a specific version:

```bash
poetry run alembic upgrade <revision_id>
```

### Downgrade Migrations

To downgrade to a previous version:

```bash
poetry run alembic downgrade <revision_id>
```

To downgrade all migrations:

```bash
poetry run alembic downgrade base
```

### Generate Migration Files

To create a new migration file:

```bash
poetry run alembic revision -m "Description of changes"
```

To auto-generate a migration based on model changes:

```bash
poetry run alembic revision --autogenerate -m "Description of changes"
```

## Testing

```bash
poetry run pytest
```

## Contributing

1. Fork the [repository](https://github.com/CarmineOptions/derisk-research)
2. Create feature branch
3. Submit pull request

Read [contribution guide](https://github.com/CarmineOptions/derisk-research/blob/master/CONTRIBUTING.md)

## License

[License details](https://github.com/CarmineOptions/derisk-research/blob/master/LICENSE.txt)