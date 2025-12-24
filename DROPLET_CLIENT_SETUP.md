# Droplet Client Setup Guide

This guide will help you set up the droplet client so Cursor can directly interact with your droplet, eliminating the need for manual copy/paste operations.

## Overview

The droplet client allows Cursor to:
- ✅ Check droplet status (services, processes, health)
- ✅ View logs in real-time
- ✅ Check git status and changes
- ✅ Execute commands remotely
- ✅ Deploy changes automatically
- ✅ Monitor system health

## Setup Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install `paramiko` (SSH library) along with other dependencies.

### 2. Configure Droplet Connection

Create a `droplet_config.json` file in your project root:

```bash
cp droplet_config.example.json droplet_config.json
```

Edit `droplet_config.json` with your droplet details:

```json
{
  "host": "123.456.789.0",
  "port": 22,
  "username": "root",
  "key_file": "C:/Users/yourname/.ssh/id_rsa",
  "project_dir": "~/stock-bot"
}
```

**Security Options:**

**Option A: SSH Key (Recommended)**
- Use `key_file` pointing to your private SSH key
- More secure, no password needed
- Example: `"key_file": "C:/Users/yourname/.ssh/id_rsa"`

**Option B: Password**
- Use `password` field
- Less secure, but simpler
- Example: `"password": "your-password"`

**Important:** Add `droplet_config.json` to `.gitignore` to avoid committing credentials!

```bash
echo "droplet_config.json" >> .gitignore
```

### 3. Test Connection

Test the connection:

```bash
python droplet_client.py
```

You should see output showing:
- Connection status
- Current droplet status
- Git status
- Recent logs

## Usage in Cursor

Once set up, you can use the droplet client in Cursor by asking natural language questions like:

### Status Queries
- "What's the status of the droplet?"
- "Check if the bot is running"
- "Show me the git status on the droplet"
- "What processes are running?"

### Log Queries
- "Show me the last 50 lines of logs"
- "What errors are in the trading log?"
- "Show me logs from the learning system"

### Git Operations
- "What's the git status on the droplet?"
- "Pull the latest changes from git"
- "Are there any uncommitted changes?"

### Deployment
- "Deploy the latest changes"
- "Pull and restart the service"

### Custom Commands
- "Run 'ps aux | grep python' on the droplet"
- "Check disk usage on the droplet"

## Example Usage in Python

```python
from droplet_client import DropletClient

# Quick status check
with DropletClient() as client:
    status = client.get_status()
    print(f"Service status: {status['service_status']}")
    print(f"Git branch: {status['git']['branch']}")
    print(f"Memory usage: {status['memory_usage']}")

# Get logs
with DropletClient() as client:
    logs = client.get_recent_logs(100, "trading.log")
    for line in logs:
        print(line)

# Deploy changes
with DropletClient() as client:
    result = client.deploy()
    if result["success"]:
        print("Deployment successful!")
    else:
        print(f"Deployment failed: {result.get('error')}")

# Execute custom command
with DropletClient() as client:
    result = client.execute_command("python3 check_learning_status.py")
    print(result["stdout"])
```

## Convenience Functions

For quick operations, use the convenience functions:

```python
from droplet_client import get_droplet_status, get_droplet_logs, get_droplet_git_status

# Quick status
status = get_droplet_status()

# Quick logs
logs = get_droplet_logs(50)

# Quick git status
git_status = get_droplet_git_status()
```

## Environment Variables Alternative

Instead of a config file, you can use environment variables:

```bash
export DROPLET_HOST="123.456.789.0"
export DROPLET_PORT="22"
export DROPLET_USER="root"
export DROPLET_KEY_FILE="C:/Users/yourname/.ssh/id_rsa"
export DROPLET_PROJECT_DIR="~/stock-bot"
```

## Troubleshooting

### Connection Failed
- Verify SSH key or password is correct
- Check that droplet is accessible (ping, SSH manually)
- Ensure firewall allows SSH (port 22)
- Try connecting manually: `ssh root@your-droplet-ip`

### Authentication Failed
- If using key file, ensure path is correct and key has proper permissions
- If using password, ensure it's correct
- Check that the user has SSH access

### Command Timeout
- Some commands may take longer (e.g., deployment)
- Increase timeout: `client.execute_command("command", timeout=300)`

### Permission Denied
- Some commands may require sudo
- Ensure the SSH user has necessary permissions
- Consider using a user with sudo access

## Security Best Practices

1. **Never commit `droplet_config.json`** - Add to `.gitignore`
2. **Use SSH keys** instead of passwords when possible
3. **Restrict SSH access** - Use firewall rules to limit access
4. **Use environment variables** in CI/CD instead of config files
5. **Rotate credentials** regularly

## Next Steps

Once set up, you can:
1. Ask Cursor to check droplet status anytime
2. Have Cursor monitor logs for errors
3. Deploy changes directly from Cursor
4. Get real-time updates on system health

Cursor will now be able to see everything happening on your droplet without you needing to manually SSH and copy/paste!

