# Derisk SDK

This project is a FastAPI-based application, set up with Poetry for dependency management and Docker for containerization.

## Requirements

- Docker
- Docker Compose

## Project Setup

### Run the Project

1. Clone git repository

```bash
git clone https://github.com/CarmineOptions/derisk-research.git
```

2. Go to `sdk/`


```bash
cd sdk 
```

3. Configure Environment Variables

Create `.env` file or just rename `.env.dev` --> `.env`

```bash
mv .env.dev .env
```

4. Provide all environment variables needed

```bash
# postgresql 
DB_HOST=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_PORT=
```

5. **Build and Run the Services**

   Use `docker-compose` to build and run the project:

   ```bash
   docker-compose up --build
   ```

   • The backend service will be accessible at http://localhost:8000.

   • The Redis service will run on port 6379.

6. **Stop the Services**

   To stop the running containers, use:

   ```bash
   docker-compose down
   ```

## Access the API

Once the services are up, visit http://localhost:8000/docs to access the interactive API documentation (Swagger UI).

## Local Development Without Docker

If you prefer running the project locally without Docker:

1. **Create a virtual environment**

   ```bash
   python -m venv .venv
   ```

2. **Activate virtual environment**

   ```bash
   source .venv/bin/activate
   ```

3. **Install Poetry**

   ```bash
   pip install poetry
   ```

4. **Install Dependencies**

   ```bash
   poetry install
   ```

5. **Activate Poetry shell**

   ```bash
   poetry shell
   ```

6. **Run the Application**

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
