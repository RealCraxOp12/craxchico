# Telegram Category Manager Bot

A Telegram bot that allows users to add and view data in different categories.

## Features

- Add data to 5 different categories:
  - Punching Bins
  - Punching Methods
  - Enroll Bins
  - Enroll Methods
  - Logs
- View saved data by category
- Data is stored separately per user
- Clean inline keyboard interface
- Async implementation using python-telegram-bot

## Installation

### 1. Install Python
Make sure you have Python 3.8 or higher installed on your system.

### 2. Install Requirements
```bash
pip install --upgrade python-telegram-bot==21.7
```

Note: If you're using Python 3.13, make sure to use version 21.7 or higher.

## Setup

### 1. Create a Bot Token from BotFather

1. Open Telegram and search for `@BotFather`
2. Start a chat with BotFather
3. Send `/newbot` command
4. Follow the instructions:
   - Choose a name for your bot (e.g., "My Category Bot")
   - Choose a username for your bot (must end with 'bot', e.g., "my_category_bot")
5. BotFather will give you a token that looks like:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
6. Copy this token

### 2. Configure the Bot

Open `telegram_bot.py` and replace `YOUR_BOT_TOKEN` with your actual token:

```python
TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
```

## Running the Bot

### On Windows:
```bash
python telegram_bot.py
```

### On Linux/Mac:
```bash
python3 telegram_bot.py
```

You should see:
```
Bot started...
```

## Usage

1. Open Telegram and search for your bot by username
2. Send `/start` to begin
3. Click "Add" to add data to a category
4. Click "View" to view saved data
5. Use `/cancel` to cancel any ongoing operation

## How It Works

- **In-Memory Storage**: Data is stored in a Python dictionary during runtime
- **Per-User Data**: Each user's data is stored separately
- **Async Operations**: Uses async/await for efficient handling
- **ConversationHandler**: Manages multi-step interactions
- **CallbackQueryHandler**: Handles button clicks

## Notes

- Data is stored in memory and will be lost when the bot restarts
- To persist data, consider using SQLite or a database
- The bot must be running continuously to respond to messages

## Troubleshooting

**Bot doesn't respond:**
- Check if the bot is running
- Verify the token is correct
- Make sure you have internet connection

**Import errors:**
- Reinstall requirements: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.8+)

**Token errors:**
- Make sure you copied the full token from BotFather
- Check for extra spaces in the token string
