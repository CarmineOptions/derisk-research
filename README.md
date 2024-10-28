# DeRisk Starknet

This project consist of a monorepo with components required for the implementation of DeRisk on Starknet.
There are several components in this repository, each with its own purpose and functionality. The main components are:
- `data_handler`
- `web_app`
- `legacy_app`
- `dashboard_app`
- `shared` - Common code shared between the components

## Data Handler
1. To set up this project run next command for local development in `derisk-research` directory:
```
docker-compose -f devops/dev/docker-compose.data-handler.yaml up --build
```
2. To run test cases for this project run next command in `derisk-research` directory:
```
make test_data_handler
```


## Legacy app
1. To set up this project run next command for local development in `derisk-research` directory:
```
make setup
```
2. To run streamlit app run next command in `derisk-research` directory:
```
make app
```

## Web app (Notification app)
1. To set up this project run next command for local development in `derisk-research` directory:
```
docker-compose -f devops/dev/docker-compose.notification-app.yaml up --build
```
