#!/bin/bash

# Life Agent Quick Start Script

echo "=================================="
echo "Life Agent Setup"
echo "=================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed."
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    echo "Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose found"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your API keys!"
    echo ""
    echo "You need:"
    echo "  1. Telegram Bot Token (get from @BotFather)"
    echo "  2. Anthropic API Key (get from console.anthropic.com)"
    echo ""
    read -p "Press Enter when you've added your API keys to .env..."
fi

# Validate .env has required keys
if grep -q "your_telegram_bot_token_here" .env || grep -q "your_anthropic_api_key_here" .env; then
    echo ""
    echo "❌ Please update .env with your actual API keys"
    echo "   Edit .env and replace the placeholder values"
    exit 1
fi

echo ""
echo "✓ Configuration looks good"
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p data/uploads data/screenshots logs
echo "✓ Directories created"
echo ""

# Build and start
echo "Building and starting Life Agent..."
echo "(This may take a few minutes the first time)"
echo ""

docker-compose up -d --build

# Wait a bit for startup
echo ""
echo "Waiting for agent to start..."
sleep 10

# Check if running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "=================================="
    echo "✓ Life Agent is Running!"
    echo "=================================="
    echo ""
    echo "📱 Next Steps:"
    echo "  1. Open Telegram"
    echo "  2. Find your bot (search for its name)"
    echo "  3. Send /start"
    echo "  4. Start talking!"
    echo ""
    echo "📊 View logs:"
    echo "  docker-compose logs -f agent"
    echo ""
    echo "🛑 Stop agent:"
    echo "  docker-compose down"
    echo ""
    echo "🔄 Restart agent:"
    echo "  docker-compose restart agent"
    echo ""
else
    echo ""
    echo "❌ Something went wrong"
    echo ""
    echo "Check logs:"
    echo "  docker-compose logs agent"
    echo ""
    echo "Common issues:"
    echo "  - Invalid API keys in .env"
    echo "  - Port conflicts"
    echo "  - Docker permissions"
    echo ""
fi
