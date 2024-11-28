# DeRisk Starknet

This project consist of a monorepo with components required for the implementation of DeRisk on Starknet.
There are several components in this repository, each with its own purpose and functionality. The main components are:
- [`data_handler`](./apps/data_handler/README.md) - Data processing and analysis component
- [`web_app`](./apps/web_app/README.md) - Main web application interface
- [`legacy_app`](./apps/legacy_app/README.md) - Legacy application functionality
- [`dashboard_app`](./apps/dashboard_app/README.md) - Analytics dashboard
- [`shared`](./apps/shared/README.md) - Common code shared between the components

## Quick Start Guide

### Prerequisites
- Docker installed on your machine (v19.03+ recommended).
- Docker Compose installed (v2.0+ recommended).

### Data Handler

The data handler component processes and manages data for the DeRisk platform.

#### Local Development

1. To set up this project run next command for local development in `derisk-research` directory:

2. Environment Configuration:
```bash
cp apps/data_handler/.env.example apps/data_handler/.env.dev
```
3. Start the Services:

```bash
docker-compose -f devops/dev/docker-compose.data-handler.yaml up --build
```
4. Stop the Services:
```bash
docker-compose -f devops/dev/docker-compose.data-handler.yaml down
```

5. To run test cases for this project run next command in `derisk-research` directory:
```bash
make test_data_handler
```

For detailed documentation, see the [Data Handler](./apps/data_handler/README.md)



## Legacy app

The legacy app provides essential functionality for data visualization and analysis through a Streamlit interface.

#### Local Development

1. To set up this project run next command for local development in `derisk-research` directory:
```bash
make setup
```

2. To run streamlit app run next command in `derisk-research` directory:
```bash
make app
```

3. Start Jupyter notebook (optional):
```bash
make notebook
```
For detailed documentation, see [`legacy_app`](./apps/legacy_app/README.md)

## Web app (Notification app)
To set up this project run next command for local development in `derisk-research` directory:

1. Environment Configuration: 
```bash
cp apps/web_app/.env.example apps/web_app/.env.dev
```

2. Start the Services:
```bash
docker-compose -f devops/dev/docker-compose.notification-app.yaml up --build
```

3. Stop the Services:
```bash
docker-compose -f devops/dev/docker-compose.notification-app.yaml down
```

## Dashboard App

Interactive dashboard application for visualizing and analyzing DeRisk data.

### Key Features
- Interactive data visualization
- Protocol statistics monitoring
- Loan portfolio analysis
- Real-time data updates
For detailed documentation, see the [Dashboard App](./apps/dashboard_app/README.md)

## Shared package (Common code shared between the components)
1. How to run test cases for shared package, run next command in root folder:
```bash
make test_shared
```