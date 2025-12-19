# Resolve Git Conflict and Deploy

## Step 1: Resolve Git Conflict

You have local changes that conflict. Discard local changes to these diagnostic scripts (they're not critical):

```bash
cd /root/stock-bot
git checkout --theirs CHECK_SUPERVISOR_OUTPUT.sh
git checkout --theirs DIAGNOSE_EMPTY_TRADES.sh
git checkout --theirs TEST_API_DIRECTLY.sh
git checkout --theirs check_risk_logs.sh
git checkout --theirs check_uw_api_usage.sh
git checkout --theirs verify_risk_integration.sh
```

## Step 2: Pull Latest Code

```bash
git pull origin main --no-rebase
```

## Step 3: Restart Supervisor

```bash
pkill -f deploy_supervisor
sleep 2
source venv/bin/activate
venv/bin/python deploy_supervisor.py
```

## Step 4: Watch for New DEBUG Logs

The new logging will show exactly what's happening. Look for these messages in the supervisor output:

- `DEBUG SYMBOL: About to call submit_entry` - Confirms it's being called
- `DEBUG SYMBOL: submit_entry completed` - Shows what happened
- `DEBUG SYMBOL: EXCEPTION in submit_entry` - Shows any errors
- `DEBUG SYMBOL: Order SUBMITTED` or `Order IMMEDIATELY FILLED` - Shows order status

## All-in-One Command

```bash
cd /root/stock-bot && \
git checkout --theirs CHECK_SUPERVISOR_OUTPUT.sh DIAGNOSE_EMPTY_TRADES.sh TEST_API_DIRECTLY.sh check_risk_logs.sh check_uw_api_usage.sh verify_risk_integration.sh && \
git pull origin main --no-rebase && \
pkill -f deploy_supervisor && \
sleep 2 && \
source venv/bin/activate && \
venv/bin/python deploy_supervisor.py
```

After this runs, watch the supervisor output for the new DEBUG messages that will show exactly why trades aren't executing.
