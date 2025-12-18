# Setup Virtual Environment and Deploy

## Quick Setup Commands

Run these commands on your droplet:

```bash
cd /root/stock-bot

# 1. Check if venv already exists
if [ -d "venv" ]; then
    echo "✅ venv exists"
else
    echo "Creating venv..."
    python3 -m venv venv
fi

# 2. Activate venv and install dependencies
source venv/bin/activate
pip install -r requirements.txt

# 3. Check for .env file (secrets)
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    echo "Loading .env file..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found"
    echo "You need to either:"
    echo "  - Create .env file with: UW_API_KEY, ALPACA_KEY, ALPACA_SECRET"
    echo "  - Or export environment variables"
fi

# 4. Verify secrets are loaded
echo "Checking environment variables..."
env | grep -E "UW_API_KEY|ALPACA_KEY|ALPACA_SECRET" || echo "⚠️  Secrets not found"

# 5. Pull latest code
git pull origin main --no-rebase

# 6. Stop existing supervisor
pkill -f deploy_supervisor

# 7. Start supervisor with venv Python
venv/bin/python deploy_supervisor.py
```

## Alternative: Create .env File

If you don't have a .env file, create one:

```bash
cd /root/stock-bot
cat > .env << 'EOF'
UW_API_KEY=your_uw_api_key_here
ALPACA_KEY=your_alpaca_key_here
ALPACA_SECRET=your_alpaca_secret_here
EOF

# Secure the file
chmod 600 .env

# Load it
export $(cat .env | grep -v '^#' | xargs)
```

## Verify Everything is Working

After starting, check:

```bash
# Check if daemon is running
ps aux | grep uw_flow_daemon

# Check if cache is being created
ls -la data/uw_flow_cache.json

# Check daemon logs
tail -f logs/uw-daemon-pc.log

# Check API usage
./check_uw_api_usage.sh
```

## If Using systemd

If you're using systemd, update the service file to use venv:

```ini
[Service]
ExecStart=/root/stock-bot/venv/bin/python /root/stock-bot/deploy_supervisor.py
EnvironmentFile=/root/stock-bot/.env
```
