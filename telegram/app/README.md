# Telegram Finance Bot

A composable Telegram bot for logging purchases with session management and flexible input parsing.

## Features

- **Session-based interactions**: Start a session with `/log-finance` and maintain context
- **Flexible input parsing**: Support for various amount formats and optional parameters
- **Composable architecture**: Each command is in a separate file for easy extension
- **Automatic session cleanup**: Sessions expire after 5 minutes of inactivity
- **Console logging**: All confirmed transactions are logged to console

## Usage

### Starting a Session

```
/log-finance
```

Or with optional parameters:

```
/log-finance date=2024-01-15 account=credit_card
```

### Input Format

The bot expects input in the format: `amount, category, date (optional), account_type (optional)`

Examples:
- `30$, food` - Uses default date (today) and account type (debit card)
- `50.25, groceries, yesterday, credit card`
- `100, entertainment, 2024-01-10, cash`

### Session Flow

1. User sends `/log-finance` (with optional parameters)
2. Bot prompts for input format
3. User enters transaction data
4. Bot displays parsed data and asks for confirmation
5. User can confirm or edit
6. Session ends and transaction is logged to console

## Architecture

### File Structure

```
app/
├── main.py                 # Main entry point with webhook handler
├── commands/
│   ├── __init__.py        # Package initialization
│   ├── base_command.py    # Base class for all commands
│   └── log_finance.py     # Log finance command handler
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Key Components

#### Main Application (`main.py`)
- Webhook endpoint for Telegram
- Session management
- Command routing
- Automatic session cleanup

#### Base Command (`commands/base_command.py`)
- Abstract base class for all commands
- Common functionality like message sending
- Standardized interface for command handlers

#### Log Finance Command (`commands/log_finance.py`)
- Handles `/log-finance` command
- Parses user input with flexible format support
- Manages session state and user confirmation

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export BOT_USERNAME="your_bot_username"
```

3. Run the application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

4. Set up webhook with Telegram:
```bash
curl -X POST "https://api.telegram.org/bot{YOUR_BOT_TOKEN}/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-domain.com/webhook"}'
```

## Adding New Commands

To add a new command:

1. Create a new file in `commands/` directory
2. Inherit from `BaseCommand`
3. Implement `handle_command()` and `handle_session_continuation()` methods
4. Add the command to the `command_handlers` mapping in `main.py`

Example:
```python
from .base_command import BaseCommand

class NewCommand(BaseCommand):
    async def handle_command(self, chat_id: int, session_data: Dict):
        # Handle initial command
        pass
    
    async def handle_session_continuation(self, chat_id: int, text: str, session_data: Dict) -> Dict:
        # Handle session continuation
        return {"session_ended": False}
```

## Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from @BotFather
- `BOT_USERNAME`: Your bot's username (without @)

## Dependencies

- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `httpx`: HTTP client for Telegram API
- `pydantic`: Data validation
- `python-multipart`: Form data parsing 