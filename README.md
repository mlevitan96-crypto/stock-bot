# Trading Bot - DigitalOcean Deployment

## Quick Start

### 1. Create Droplet
- Recommended: Ubuntu 22.04 LTS
- Size: 2 vCPU, 4GB RAM minimum
- Enable monitoring

### 2. Install Dependencies
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv
cd /opt
git clone <your-repo> trading-bot
cd trading-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment (SECURITY CRITICAL)

**Option A: DigitalOcean App Platform (Recommended)**
Use DigitalOcean's built-in secret management:
1. Go to App Platform → Settings → App-Level Environment Variables
2. Add each secret as an "Encrypted" variable
3. Never store secrets in files on the droplet

**Option B: Droplet with Environment File**
```bash
cp .env.example .env
nano .env  # Edit with your API keys
chmod 600 .env  # Restrict permissions
```

⚠️ **NEVER commit .env with real credentials to git**
⚠️ **Add .env to .gitignore**

### 4. Run as Systemd Service
Create `/etc/systemd/system/trading-bot.service`:
```ini
[Unit]
Description=Algorithmic Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/trading-bot
EnvironmentFile=/opt/trading-bot/.env
ExecStart=/opt/trading-bot/venv/bin/python deploy_supervisor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

### 5. Monitor
```bash
sudo journalctl -u trading-bot -f
curl http://localhost:8080/health
```

## Files

| File | Purpose |
|------|---------|
| `main.py` | Core trading logic |
| `deploy_supervisor.py` | Process manager |
| `dashboard.py` | Web dashboard (port 5000) |
| `config/registry.py` | Configuration defaults |
| `start.sh` | Manual startup script |

## Ports

- **5000**: Dashboard (web UI)
- **8080**: Health endpoint

## Logs

All services log to stdout. With systemd, view via:
```bash
journalctl -u trading-bot --since "1 hour ago"
```

## Architecture

```
deploy_supervisor.py (parent)
├── main.py (trading-bot) - Executes trades
├── dashboard.py - Position monitoring UI
└── Health checks every 30s
```

The supervisor auto-restarts crashed children with exponential backoff.
