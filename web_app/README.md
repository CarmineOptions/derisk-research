# DeRisk Alert

# How it works:
![A diagram that ilustrates how this app works](docs/how-it-works.drawio.png)
### `Here is a demo video how it works` [Click](https://drive.google.com/file/d/1TYwEx6PWvPerrJSfiePQzZEtbj53Yn_g/view?usp=sharing)

### When the `health ratio` is appropriate to the value you 
### have set you will be notified via `Telegram`

![An image that ilustrates a notification](docs/notification.png)

# Database ordering:
![A diagram that ilustrates the ordering of the DB](docs/db-ordering.png)

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
IP_INFO_TOKEN=#
TELEGRAM_TOKEN= # token telegram from botfather
GS_BUCKET_NAME=#
GS_BUCKET_URL=#
REDIS_HOST=redis
REDIS_PORT=6379
CHECK_DATA_CHANGES_PERIOD=# in seconds
```

### 5. Build your docker containers

```bash
docker-compose up -d --build
```

#### Stop your containers

```bash
docker-compose down
```
