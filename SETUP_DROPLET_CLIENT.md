# Droplet Client Setup - SSH Config Method

## Current Status

✅ **SSH Configuration:** CONFIGURED AND WORKING  
✅ **Method:** SSH Config File (host: `alpaca`)

## Step 1: Add Config File to .gitignore

**Why:** We don't want to accidentally commit your droplet credentials to git.

**Action:** Add `droplet_config.json` to your `.gitignore` file (already done).

**Verify it worked:**
```bash
cat .gitignore | grep droplet_config
```

You should see `droplet_config.json` in the output.

---

## Step 2: Install the SSH Library

**Why:** We need `paramiko` to connect to your droplet via SSH.

**Action:** Install the dependency.

```bash
pip install paramiko==3.4.0
```

**Verify it worked:**
```bash
python -c "import paramiko; print('paramiko installed successfully')"
```

You should see: `paramiko installed successfully`

---

## Step 3: Create Your Droplet Config File

**Why:** The client needs to know which SSH config host to use.

**Action:** Create `droplet_config.json` with SSH config host.

```bash
cat > droplet_config.json << 'EOF'
{
  "host": "alpaca",
  "port": 22,
  "username": "root",
  "use_ssh_config": true,
  "project_dir": "~/stock-bot"
}
EOF
```

**Note:** This uses your SSH config file (`~/.ssh/config`) with host alias `alpaca`. Make sure you have `alpaca` configured in your SSH config with the correct hostname, user, and identity file.

---

## Step 4: Verify SSH Config

**Why:** Make sure your SSH config has the `alpaca` host configured.

**Action:** Test SSH connection manually.

```bash
ssh alpaca "echo 'SSH config working'"
```

**Expected Output:**
```
SSH config working
```

If this works, your SSH config is set up correctly.

---

## Step 5: Test the Connection

**Why:** Make sure everything is configured correctly before using it.

**Action:** Test the droplet client connection.

```bash
python test_ssh_connection.py
```

**Expected Output:**
```
============================================================
TESTING SSH CONNECTION TO DROPLET
============================================================

[OK] Config loaded successfully
  Host: 104.236.102.57
  Username: root
  Port: 22

Testing connection...
[OK] Connection successful!
  Droplet: 104.236.102.57
  Project Dir: ~/stock-bot

Testing command execution...
[OK] Command executed (exit code: 0)
  Output:
/root/stock-bot
Test command successful
...

[OK] ALL TESTS PASSED - SSH CONNECTION WORKING
============================================================
```

**If you see an error:**

**Error: "Droplet configuration not found"**
- Make sure `droplet_config.json` exists in the project root
- Check that the file has valid JSON

**Error: "Authentication failed"**
- Verify SSH config host `alpaca` exists in `~/.ssh/config`
- Test SSH connection manually: `ssh alpaca`
- Check SSH key is accessible

**Error: "Connection failed" or "Connection timeout"**
- Verify SSH config hostname is correct
- Check that the droplet is running and accessible
- Test SSH manually: `ssh alpaca`

---

## Step 6: Verify It Works with a Quick Test

**Why:** Confirm the client can actually interact with your droplet.

**Action:** Run a simple test command.

```python
python -c "from droplet_client import DropletClient; client = DropletClient(); print('Connected!'); status = client.get_status(); print(f\"Service: {status['service_status']}\"); print(f\"Git branch: {status['git']['branch']}\"); client.close()"
```

**Expected Output:**
```
Connected!
Service: active
Git branch: main
```

---

## Step 7: Test Common Operations

**Why:** Make sure all the features work as expected.

### Test 1: Get Git Status
```python
python -c "from droplet_client import get_droplet_git_status; import json; print(json.dumps(get_droplet_git_status(), indent=2))"
```

### Test 2: Get Recent Logs
```python
python -c "from droplet_client import get_droplet_logs; logs = get_droplet_logs(10); print('\\n'.join(logs[-10:]))"
```

### Test 3: Get Full Status
```python
python -c "from droplet_client import get_droplet_status; import json; print(json.dumps(get_droplet_status(), indent=2))"
```

---

## Step 8: You're Done! 🎉

**What you can now do:**

1. **Ask Cursor natural language questions:**
   - "What's the status of the droplet?"
   - "Show me the last 50 lines of logs"
   - "What's the git status on the droplet?"
   - "Deploy the latest changes"

2. **Use in Python scripts:**
   ```python
   from droplet_client import DropletClient
   
   with DropletClient() as client:
       status = client.get_status()
       print(status)
   ```

3. **Quick convenience functions:**
   ```python
   from droplet_client import get_droplet_status, get_droplet_logs
   
   status = get_droplet_status()
   logs = get_droplet_logs(50)
   ```

---

## Troubleshooting

### SSH Config Not Found
If your SSH config doesn't have `alpaca`:

1. Add it to `~/.ssh/config`:
   ```
   Host alpaca
       HostName 104.236.102.57
       User root
       IdentityFile ~/.ssh/id_ed25519
       Port 22
   ```

2. Test it: `ssh alpaca "echo test"`

### Still Having Issues?
1. Test SSH connection manually first:
   ```bash
   ssh alpaca
   ```

2. If manual SSH works but the client doesn't:
   - Check the config file JSON is valid
   - Verify `use_ssh_config` is set to `true`
   - Make sure SSH config host `alpaca` exists

3. Check the error message - it usually tells you what's wrong!

---

## Next: Start Using It!

Once setup is complete, you can ask Cursor things like:

- "Check the droplet status"
- "Show me what's running on the droplet"
- "What's the git status on the droplet?"
- "Pull the latest changes and deploy"
- "Show me the last 100 lines of the trading log"

Cursor will handle all the SSH connections and commands for you!

---

**Status:** ✅ **COMPLETE - Using SSH config method**
