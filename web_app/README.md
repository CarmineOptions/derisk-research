# DeRisk Alert

# How it works:
![A diagram that illustrates how this app works](docs/how-it-works.drawio.png)
### `Here is a demo video how it works` [Click](https://drive.google.com/file/d/1TYwEx6PWvPerrJSfiePQzZEtbj53Yn_g/view?usp=sharing)

### When the `health ratio` is appropriate to the value you 
### have set you will be notified via `Telegram`

![An image that illustrates a notification](docs/notification.png)

# Database ordering:
![A diagram that illustrates the ordering of the DB](docs/db-ordering.png)

## Requirements
 - python3.11 
 - poetry
 - docker
 - docker-compose

## How to get Telegram Token:

### 1. To get a token and create a chatbot, you need to find a bot named BotFather in the Telegram messenger.
![An image that shows how to find bot father in telegram](docs/find-bot-father.jpg)

### 2. In the BotFather bot, you need to write the command `/newbot`. After that, BotFather will prompt you to enter:
- the name of your bot that users will see;
- uri of the bot, i.e. the link to the bot that will be added to the link https://t.me/{youruri}.
![An image that shows how to create a new bot](docs/newbot-botfather.jpg)

### 3. After the data is entered and it has passed validation, BotFather will respond with a message that will contain the API token of the created bot.
![An image that shows how to get a created token](docs/get-token.jpg)

### 4. Done! At this moment, the bot has already been created, and it is possible to subscribe to it by finding it in Telegram search or by following the link. 

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
