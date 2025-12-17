# Zero-Downtime Deployment System

## Overview

Production-grade A/B deployment system that enables updates during market hours with zero downtime and automatic rollback.

## Features

✅ **Zero Downtime** - Updates happen without interrupting trading  
✅ **A/B Switching** - Two instances (A and B) for seamless transitions  
✅ **Health Checks** - Automatic validation before switching  
✅ **Auto Rollback** - Instant revert if new instance fails  
✅ **State Preservation** - Cache, positions, and logs preserved  
✅ **Single Command** - One script does everything  
✅ **Market Hours Safe** - Designed for live trading environments  

## How It Works

1. **Two Instances**: Maintains two separate instances (A and B)
2. **Staging Update**: Updates the inactive instance with latest code
3. **Health Validation**: Verifies new instance is healthy before switch
4. **Traffic Switch**: Seamlessly switches to new instance
5. **Rollback Ready**: Keeps old instance running for instant rollback

## Usage

### Single Command Deployment

```bash
cd /root/stock-bot && chmod +x deploy.sh && ./deploy.sh
```

That's it! The script will:
- Clone current codebase to staging instance
- Pull latest code from git
- Start staging instance on alternate port
- Health check the staging instance
- Switch traffic to new instance
- Verify new instance is working
- Keep old instance running for rollback

### Manual Rollback

If you need to rollback manually:

```bash
cd /root/stock-bot
python3 -c "
from zero_downtime_deploy import ZeroDowntimeDeployer
deployer = ZeroDowntimeDeployer()
deployer._rollback('Manual rollback requested')
"
```

## Architecture

```
/root/stock-bot/
├── instance_a/          # Instance A (port 5000)
├── instance_b/          # Instance B (port 5001)
├── data/                # Shared data (symlinked)
├── state/               # Shared state (symlinked)
├── logs/                # Shared logs (symlinked)
└── deploy.sh            # Deployment script
```

## Health Checks

The system performs health checks:
- **Before Switch**: Validates staging instance is healthy
- **After Switch**: Verifies active instance remains healthy
- **Auto Rollback**: Reverts if health check fails

Health endpoint: `http://localhost:{port}/health`

## State Management

Deployment state is stored in:
- `state/deployment_state.json` - Current active instance and history

## Safety Features

1. **Rate Limiting**: Prevents excessive deployments
2. **Health Validation**: Multiple health check attempts
3. **Automatic Rollback**: Instant revert on failure
4. **State Preservation**: Shared data/logs/state directories
5. **Process Management**: Proper cleanup of old processes

## Best Practices

1. **Test First**: Always test in staging before production
2. **Market Hours**: Safe to deploy during market hours
3. **Monitor**: Watch logs after deployment
4. **Rollback Ready**: Keep old instance running for quick revert

## Troubleshooting

### Deployment Fails

Check logs:
```bash
tail -f logs/deployment.log
```

### Health Check Fails

Verify instance is running:
```bash
ps aux | grep dashboard
curl http://localhost:5000/health
curl http://localhost:5001/health
```

### Manual Cleanup

If needed, clean up instances:
```bash
cd /root/stock-bot
pkill -f "dashboard.py"
rm -rf instance_a instance_b
```

## Integration with Supervisor

The deployment system works alongside your existing supervisor:
- Supervisor manages: trading-bot, uw-daemon, heartbeat-keeper
- Deployment manages: dashboard instances (A/B switching)

## Next Steps

1. Run first deployment: `./deploy.sh`
2. Monitor health: Check dashboard after switch
3. Verify trading: Ensure bot continues operating
4. Keep deploying: Use same command for all updates
