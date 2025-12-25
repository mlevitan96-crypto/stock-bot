# Droplet Client Setup Guide - SSH Config Method

## Current Status

✅ **SSH Configuration:** CONFIGURED AND WORKING  
✅ **Method:** SSH Config File (host: `alpaca`)  
✅ **Connection:** Tested and verified

## Overview

The droplet client allows Cursor to:
- ✅ Check droplet status (services, processes, health)
- ✅ View logs in real-time
- ✅ Check git status and changes
- ✅ Execute commands remotely
- ✅ Deploy changes automatically
- ✅ Monitor system health

## Configuration

**SSH Config Host:** `alpaca` (configured in `~/.ssh/config`)

**Configuration File:** `droplet_config.json`
```json
{
  "host": "alpaca",
  "port": 22,
  "username": "root",
  "use_ssh_config": true,
  "project_dir": "~/stock-bot"
}
```

**How It Works:**
- Uses your standard SSH config file (`~/.ssh/config`)
- Automatically resolves hostname, username, port, and key file from SSH config
- No passwords stored in config files
- Secure and standard approach

## Usage in Cursor

Once configured, you can use the droplet client in Cursor by asking natural language questions like:

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

## Troubleshooting

### Connection Failed
- Verify SSH config host `alpaca` exists in `~/.ssh/config`
- Test SSH connection manually: `ssh alpaca "echo test"`
- Check that `droplet_config.json` exists with `"host": "alpaca"` and `"use_ssh_config": true`
- Ensure firewall allows SSH (port 22)

### Authentication Failed
- Verify SSH key is loaded in SSH agent or key file is accessible
- Test SSH connection manually: `ssh alpaca`
- Check SSH config has correct identity file

### Command Timeout
- Some commands may take longer (e.g., deployment)
- Increase timeout: `client.execute_command("command", timeout=300)`

### Permission Denied
- Some commands may require sudo
- Ensure the SSH user has necessary permissions
- Consider using a user with sudo access

## Security Best Practices

1. **Never commit `droplet_config.json`** - Already in `.gitignore`
2. **Use SSH config** - Standard and secure approach
3. **Restrict SSH access** - Use firewall rules to limit access
4. **Rotate credentials** regularly

## Next Steps

Once set up, you can:
1. Ask Cursor to check droplet status anytime
2. Have Cursor monitor logs for errors
3. Deploy changes directly from Cursor
4. Get real-time updates on system health

Cursor will now be able to see everything happening on your droplet without you needing to manually SSH and copy/paste!

---

**Status:** ✅ **COMPLETE - Fully configured and working**
