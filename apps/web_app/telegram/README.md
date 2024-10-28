# Notification Bot

This is a Telegram bot built using the aiogram library for Python. The bot allows users to subscribe to notifications and manage them through a menu-based interface. Users can view their current notifications, delete specific notifications, or unsubscribe from all notifications.

## Features

- Subscribe to notifications by sending the `/start` command with a deep link
- View a list of current notifications
- Delete individual notifications
- Unsubscribe from all notifications
- Pagination for navigating through multiple notifications

## Installation

1. Install the required dependencies:

    Current work directory is web_app
    ```bash
    pip install poetry
    poetry install .
    ```

2. Set up the database and configure the necessary environment variables (views in web_app README).

3. Run the bot:

```bash
python -m telegram
```

## Usage

### Subscribing to Notifications

To subscribe to notifications, send the `/start` command followed by a deep link to the bot. This will register your Telegram ID in the database and allow you to receive notifications.

![Subscribe to Notifications](assets/subscribe.png)

### Accessing the Main Menu

To access the main menu, either click the "Go to menu" button or send the `/menu` command to the bot.

![Main Menu](assets/main_menu.png)

### Viewing Notifications

From the main menu, click the "Shows notifications" button to view your current notifications. If you have multiple notifications, pagination buttons will be displayed to navigate through them.

![View Notifications](assets/view_notifications.png)

### Deleting a Notification

To delete a specific notification, click the "Delete" button while viewing the notification details.

![Delete Notification](assets/delete_notification.png)

After clicking delete

![Post confirm delete Notification](assets/post_confirm_delete_notification.png)

### Unsubscribing from All Notifications

To unsubscribe from all notifications, click the "Unsubscribe all" button in the main menu and confirm your action.

![Unsubscribe from All Notifications](assets/unsubscribe_all.png)

After clicking Unsubscribe all

![Post confirm Unsubscribe from All Notifications](assets/post_confim_unsubscribe_all.png)