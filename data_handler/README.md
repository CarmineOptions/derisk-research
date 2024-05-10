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
DERISK_API_ENDPOINT=#
```

### 5. Build your docker containers

```bash
docker-compose up -d --build
```

#### Stop your containers

```bash
docker-compose down
```

