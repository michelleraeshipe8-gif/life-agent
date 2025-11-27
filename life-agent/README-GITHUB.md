# Life Agent

Your personal AI assistant via Telegram.

## Features

- Personal memory
- Smart reminders
- Calendar management
- Financial tracking
- Relationship management
- Browser automation

## Quick Deploy

See [DEPLOY.md](DEPLOY.md) for 5-minute Railway deployment.

## Local Setup

```bash
pip install -r requirements.txt
python main.py
```

Add your API keys to `.env` file.

## Environment Variables

Required:
- `TELEGRAM_BOT_TOKEN` - Get from @BotFather
- `ANTHROPIC_API_KEY` - Get from console.anthropic.com
- `DATABASE_URL` - SQLite or PostgreSQL

## Usage

Message your bot on Telegram:
- `/start` - Initialize
- "Remind me to..." - Set reminders
- "I spent $..." - Track expenses
- Natural conversation works!

## License

MIT
