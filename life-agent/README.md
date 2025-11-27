# 🤖 Life Agent - Your Personal AI Assistant

A powerful, modular AI agent that helps you manage your daily life through Telegram. Built with Claude API for intelligence, browser automation capabilities, and an extensible plugin system.

## ✨ Features

### Core Capabilities
- **Natural conversation** - Talk naturally, no rigid commands
- **Personal memory** - Remembers important information about you
- **Smart reminders** - Time-based, location-based, and context-aware
- **Calendar management** - View and create events
- **Financial tracking** - Track expenses, income, and budgets
- **Relationship management** - Track contacts and interactions
- **Browser automation** - Can interact with any website
- **Modular plugin system** - Easy to add new features

### Currently Enabled Plugins (Out of the Box)
1. **Personal Memory** - Remember and recall your information
2. **Smart Reminders** - Intelligent reminder system
3. **Calendar Integration** - Manage your schedule
4. **Basic Financial** - Track money and budgets
5. **Relationship Manager** - Nurture your relationships

### Available Plugins (Ready to Enable)
- Health Tracker
- Home Management
- Travel Planner
- Shopping & Deals
- Content Curator
- Learning Tracker
- Mental Health Journal
- Photo Organizer
- Voice Interface
- And more!

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Telegram account
- Anthropic API key (Claude)

### 1. Get Your API Keys

#### Telegram Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions
3. Save your bot token - you'll need it soon

#### Anthropic API Key
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key and save it

### 2. Clone and Configure

```bash
# Clone or download this folder
cd life-agent

# Copy environment template
cp .env.example .env

# Edit .env file with your keys
nano .env  # or use any text editor
```

Update these values in `.env`:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DB_PASSWORD=choose_a_secure_password
```

### 3. Deploy with Docker

```bash
# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f agent

# You should see: "✓ Life Agent is running!"
```

### 4. Start Using

1. Open Telegram
2. Find your bot (search for the name you gave it)
3. Send `/start`
4. Start talking naturally!

## 💬 How to Use

### Basic Interaction

Just talk naturally! Examples:

```
You: Hey, remind me to call mom tomorrow at 2pm
Agent: ✓ Reminder set for December 27 at 02:00 PM

You: I spent $45 on groceries
Agent: ✓ Logged: $45.00 spent on food 🍔

You: What's on my calendar today?
Agent: 📅 Events for Thursday, December 26:
       • 10:00 AM - Team meeting
       • 02:00 PM - Doctor appointment

You: Add contact: John Smith, friend, birthday March 15
Agent: ✓ Added 👋 John Smith (friend)
       🎂 Birthday: March 15
```

### Commands

- `/start` - Initialize and get welcome message
- `/help` - See all available commands
- `/plugins` - List loaded plugins

### Advanced Usage

**Send photos:** Take a picture of a receipt, product, or anything
**Voice messages:** Talk instead of type
**Documents:** Upload PDFs, CSVs, etc.

## 🔧 Configuration

### Plugin Configuration

Edit `config/plugins.yaml` to enable/disable plugins:

```yaml
enabled_plugins:
  - memory
  - conversation
  - personal_memory
  - smart_reminders
  - calendar_integration
  - basic_financial
  - relationship_manager
  # - health_tracker  # Uncomment to enable
  # - voice_interface
```

### Plugin Settings

Customize plugin behavior in the same file:

```yaml
plugin_settings:
  smart_reminders:
    location_based: true
    context_aware: true
  
  basic_financial:
    auto_categorize: true
    monthly_budget: 2000
  
  relationship_manager:
    check_in_interval_days: 14
    birthday_reminder_days: 7
```

## 📦 Adding More Features

### Method 1: Enable Existing Plugins

```bash
# Edit plugins config
nano config/plugins.yaml

# Uncomment the plugins you want
# Then restart
docker-compose restart agent
```

### Method 2: Build Custom Plugins

See `PLUGIN_DEVELOPMENT.md` for full guide. Quick example:

```python
# plugins/my_plugin.py
from core.plugin import Plugin

class MyPlugin(Plugin):
    name = "My Plugin"
    description = "Does something cool"
    keywords = ["my", "plugin"]
    
    async def initialize(self):
        pass
    
    async def handle(self, message, context):
        if "my plugin" in message.lower():
            return "Hello from my plugin!"
        return None
```

Add to `config/plugins.yaml`:
```yaml
enabled_plugins:
  - my_plugin
```

Restart agent - done!

## 🗄️ Data Storage

All your data is stored locally in:
- **Database:** `postgres_data/` (in Docker volume)
- **Uploads:** `data/uploads/` (photos, documents)
- **Screenshots:** `data/screenshots/` (browser automation)
- **Logs:** `logs/` (application logs)

### Backup Your Data

```bash
# Backup database
docker-compose exec db pg_dump -U agent lifeagent > backup.sql

# Backup files
tar -czf data-backup.tar.gz data/ logs/
```

### Restore Data

```bash
# Restore database
cat backup.sql | docker-compose exec -T db psql -U agent lifeagent

# Restore files
tar -xzf data-backup.tar.gz
```

## 🌐 Deployment Options

### Local (Your Computer)

What you've already done! Runs on your machine.

**Pros:** Private, no ongoing costs
**Cons:** Computer must be on for agent to work

### Cloud Server (VPS)

Deploy to DigitalOcean, AWS, Linode, etc.

```bash
# On your VPS
git clone <your-repo>
cd life-agent
cp .env.example .env
# Edit .env with your keys
docker-compose up -d
```

**Pros:** Always available, access from anywhere
**Cons:** ~$5-20/month for hosting

### Recommended VPS Providers
- DigitalOcean: $6/month droplet
- Linode: $5/month
- AWS Lightsail: $5/month
- Hetzner: €4.5/month

## 📊 Monitoring

### Check Status

```bash
# View logs
docker-compose logs -f agent

# Check running containers
docker-compose ps

# Resource usage
docker stats
```

### Common Issues

**Agent not responding:**
```bash
# Restart
docker-compose restart agent

# Check logs for errors
docker-compose logs agent
```

**Database connection issues:**
```bash
# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

**Plugin errors:**
- Check `logs/agent.log` for details
- Verify plugin configuration in `config/plugins.yaml`
- Ensure plugin dependencies are installed

## 🔒 Security & Privacy

### Data Privacy
- All data stored locally (or on your VPS)
- No data sent to third parties except:
  - Anthropic (Claude API) - for AI processing
  - Telegram - for bot communication

### API Key Security
- Never commit `.env` file to git
- Use strong database password
- Rotate API keys periodically

### Access Control
- Only you can talk to your bot (by default)
- Bot token acts as authentication
- Keep bot token secret

## 🛠️ Development

### Running Without Docker

```bash
# Install Python 3.11+
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Set up database
createdb lifeagent
alembic upgrade head

# Run
python main.py
```

### Testing Plugins

```bash
# Add test plugin to plugins/
# Enable in config/plugins.yaml
# Restart agent
docker-compose restart agent

# Test via Telegram
```

## 📚 Advanced Features

### Browser Automation

The agent can control a web browser to:
- Set up your Shopify store
- Search for products on Alibaba
- Post to Instagram
- Scrape competitor prices
- Fill out forms
- And much more!

Example:
```
You: Search Alibaba for rose quartz rollers under $8
Agent: [Opens browser, searches, scrapes results]
       Found 10 options:
       1. $6.80/unit (MOQ 50) - Gold Supplier ⭐4.8
       ...
```

### Scheduled Tasks

Plugins can run tasks on schedule:
- Morning summaries
- Budget alerts
- Birthday reminders
- Relationship check-ins

Configure in plugin settings.

### Multi-Modal Input

- **Photos:** OCR text, analyze images, find similar products
- **Voice:** Transcribe and process (with voice plugin)
- **Documents:** Extract data from PDFs, receipts, etc.

## 🤝 Support

### Getting Help

1. Check `logs/agent.log` for errors
2. Review plugin documentation
3. Check configuration files

### Contributing

Want to add features? Create new plugins and share!

### Extending the Agent

The modular architecture makes it easy to add:
- New plugins for specific tasks
- Custom integrations (APIs, databases)
- Advanced AI capabilities
- Multi-agent coordination

## 📈 What's Next?

### Roadmap
- [ ] Web dashboard interface
- [ ] Voice interface (hands-free)
- [ ] Multi-agent orchestration
- [ ] Advanced analytics
- [ ] Mobile app
- [ ] Plugin marketplace

### Your Ideas?

This is your agent - customize it however you want!

## 📝 License

MIT License - Use it however you want!

---

## 🎉 You're All Set!

Your Life Agent is ready to help you manage everything. Start with simple requests and explore what it can do!

Questions? Just ask your agent: "What can you do?" or "Help me get started"
