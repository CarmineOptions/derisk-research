# DeRisk Dashboard App

Interactive dashboard application for visualizing and analyzing DeRisk data.


## Prerequisites

- Python 3.11+
- Poetry
- Docker 

## Setup

### Local Development

1. Install dependencies:
```bash
./setup.sh
```

2. Run the dashboard:
```bash
poetry run python dashboard.py
```

### Docker Setup

1. Build the image:


2. Run the container:

3. stop container:

## Key Features

- Interactive data visualization
- Protocol statistics monitoring
- Loan portfolio analysis
- Real-time data updates

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
