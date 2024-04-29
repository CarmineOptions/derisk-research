# DeRisk Alert

## Requirements
 - python3.11 
 - poetry

# Setup

### 1. Clone git repository

```bash
git clone https://github.com/CarmineOptions/derisk-research.git
```

### 2. Go to `web_app/`


```bash
cd web_app 
```

### 3. Set up `.env` file

Create `.env` file or just rename `.env.example` --> `.env`

```bash
mv .env.example .env
```

### 4. Provide all environment varibles needed

```bash
DB_NAME=#
DB_USER=#
DB_PASSWORD=#
DB_HOST=db
DB_PORT=#
```

### 5. Build your docker containers

```bash
docker-compose up -d --build
```

#### Stop your containers

```bash
docker-compose down
```
