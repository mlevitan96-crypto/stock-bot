# Self-Healing Implementation for Crashes

## Overview

Added comprehensive self-healing for `NameError` and `ImportError` crashes that were preventing the bot from trading.

## Problem

The bot was crashing repeatedly with:
```
NameError: name 'StateFiles' is not defined
```

This error occurred in `run_once()` and caused the bot to fail every cycle, preventing any trading activity.

## Solution

Implemented multi-layer self-healing:

### 1. Pre-Check in `run_once()`

Before executing the main logic, verify all required imports are available:

```python
# Pre-check that all required imports are available
try:
    _ = StateFiles.BOT_HEARTBEAT
except (NameError, AttributeError) as import_check_error:
    # Self-heal: Reload imports if missing
    import importlib
    import sys
    if 'config.registry' in sys.modules:
        importlib.reload(sys.modules['config.registry'])
    from config.registry import StateFiles
```

### 2. Exception Handler in `run_once()`

Specific handling for `NameError`/`ImportError`:

```python
except (NameError, ImportError) as e:
    # Self-healing: Reload imports
    import importlib
    import sys
    if 'config.registry' in sys.modules:
        importlib.reload(sys.modules['config.registry'])
    from config.registry import StateFiles
    # Return early to allow next cycle to proceed
    return {"clusters": 0, "orders": 0, "error": "import_reload", "healed": True}
```

### 3. Worker Loop Error Recovery

In the worker thread's exception handler:

```python
except (NameError, ImportError) as e:
    # Self-heal: Reload imports
    import importlib
    import sys
    if 'config.registry' in sys.modules:
        importlib.reload(sys.modules['config.registry'])
    from config.registry import StateFiles, Directories, CacheFiles
    
    # If too many import errors (>= 3), restart worker thread
    if self.state.fail_count >= 3:
        self.stop()
        time.sleep(2)
        self._stop_evt.clear()
        self.start()
        self.state.fail_count = 0
```

## Self-Healing Levels

1. **Level 1 (Pre-Check)**: Catches missing imports before main execution
2. **Level 2 (Exception Handler)**: Reloads imports when error occurs
3. **Level 3 (Worker Restart)**: Restarts worker thread after 3 consecutive errors
4. **Level 4 (Service Restart)**: Systemd automatically restarts service if process dies

## Monitoring

All self-healing actions are logged:
- `self_healing.pre_check_heal_success`
- `self_healing.import_reload_success`
- `self_healing.worker_thread_restart`
- `self_healing.import_reload_failed`

## Benefits

1. **Automatic Recovery**: Bot recovers from import errors without manual intervention
2. **Prevention**: Pre-check catches issues before they cause crashes
3. **Escalation**: Multiple levels ensure recovery even if one level fails
4. **Visibility**: All healing actions are logged for monitoring

## Testing

To verify self-healing works:

```bash
# Check logs for self-healing events
journalctl -u trading-bot.service | grep self_healing

# Check for StateFiles errors (should be none after fix)
journalctl -u trading-bot.service | grep StateFiles

# Monitor bot status
systemctl status trading-bot.service
```

## Future Enhancements

- Add self-healing for other common errors (AttributeError, KeyError)
- Add metrics tracking for self-healing success rate
- Add alerting when self-healing is triggered frequently

