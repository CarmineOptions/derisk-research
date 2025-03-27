# DeRisk Alert

# How it works:

This section provides an overview of how the DeRisk Alert system operates.
![A diagram that illustrates how this app works](docs/how-it-works.drawio.png)

### Demo Video
### `Here is a demo video of how it works` [Click](https://drive.google.com/file/d/1TYwEx6PWvPerrJSfiePQzZEtbj53Yn_g/view?usp=sharing)

### Notification System
### When the `health ratio` is appropriate to the value you 
### have set you will be notified via `Telegram`

![An image that illustrates a notification](docs/notification.png)

# Database Structure:


This diagram shows the ordering and structure of the database for the DeRisk Alert system:
![A diagram that illustrates the ordering of the DB](docs/db-ordering.png)

## Requirements
 - python3.11 
 - poetry
 - docker
 - docker-compose

## Telegram Bot Setup

[This section moved to /apps/shared/telegram_app/README.md](../shared/telegram_app/README.md)


### 5. Build your docker containers

```bash
docker-compose up -d --build
```

#### 6. Stop your containers

```bash
docker-compose down
```
