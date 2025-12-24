# Droplet Client Setup - Step by Step Guide

Follow these steps in order. Each step has copy/paste commands ready to use.

---

## Step 1: Add Config File to .gitignore

**Why:** We don't want to accidentally commit your droplet credentials to git.

**Action:** Add `droplet_config.json` to your `.gitignore` file.

```bash
echo "droplet_config.json" >> .gitignore
```

**Verify it worked:**
```bash
cat .gitignore | grep droplet_config
```

You should see `droplet_config.json` in the output.

---

## Step 2: Install the SSH Library

**Why:** We need `paramiko` to connect to your droplet via SSH.

**Action:** Install the new dependency.

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

**Why:** The client needs to know how to connect to your droplet.

**Action:** Create `droplet_config.json` with your droplet connection details.

**Option A: Using SSH Key (Recommended - More Secure)**

Create the file with this content (replace with your actual values):

```bash
cat > droplet_config.json << 'EOF'
{
  "host": "YOUR_DROPLET_IP_HERE",
  "port": 22,
  "username": "root",
  "key_file": "C:/Users/markl/.ssh/id_rsa",
  "project_dir": "~/stock-bot"
}
EOF
```

**Then edit it with your actual values:**
- Replace `YOUR_DROPLET_IP_HERE` with your droplet's IP address
- Replace `C:/Users/markl/.ssh/id_rsa` with the path to your SSH private key (if different)

**Option B: Using Password (Less Secure, But Simpler)**

If you don't have an SSH key set up, use password instead:

```bash
cat > droplet_config.json << 'EOF'
{
  "host": "YOUR_DROPLET_IP_HERE",
  "port": 22,
  "username": "root",
  "password": "YOUR_PASSWORD_HERE",
  "project_dir": "~/stock-bot"
}
EOF
```

**Then edit it with your actual values:**
- Replace `YOUR_DROPLET_IP_HERE` with your droplet's IP address
- Replace `YOUR_PASSWORD_HERE` with your droplet password

**Note:** If you're not sure which option to use, try Option A first. If you don't have an SSH key, you can generate one or use Option B.

---

## Step 4: Find Your SSH Key Path (If Using Option A)

**Why:** We need the exact path to your SSH private key.

**Action:** Find where your SSH key is located.

**On Windows (PowerShell):**
```powershell
Test-Path $env:USERPROFILE\.ssh\id_rsa
```

If it returns `True`, your key is at: `C:/Users/markl/.ssh/id_rsa` (replace `markl` with your username)

**List all SSH keys:**
```powershell
Get-ChildItem $env:USERPROFILE\.ssh\
```

**If you don't have an SSH key yet, you can generate one:**
```powershell
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

Then copy your public key to the droplet:
```powershell
type $env:USERPROFILE\.ssh\id_rsa.pub
```

Copy the output and add it to your droplet's `~/.ssh/authorized_keys` file.

---

## Step 5: Test the Connection

**Why:** Make sure everything is configured correctly before using it.

**Action:** Test the droplet client connection.

```bash
python droplet_client.py
```

**Expected Output:**
```
Droplet Client - Testing Connection
============================================================
Connected to: YOUR_DROPLET_IP
Status:
{
  "timestamp": "...",
  "host": "...",
  "service_status": "active",
  "process_count": 3,
  ...
}
```

**If you see an error:**

**Error: "Droplet configuration not found"**
- Make sure `droplet_config.json` exists in the project root
- Check that the file has valid JSON

**Error: "Authentication failed"**
- If using key file: Check the path is correct and the key has proper permissions
- If using password: Verify the password is correct
- Try connecting manually: `ssh root@YOUR_DROPLET_IP`

**Error: "Connection failed" or "Connection timeout"**
- Verify the droplet IP is correct
- Check that the droplet is running and accessible
- Try pinging: `ping YOUR_DROPLET_IP`
- Check firewall allows SSH (port 22)

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

### Can't Find SSH Key
If you're on Windows and can't find your SSH key:

1. Check if it exists:
   ```powershell
   Test-Path $env:USERPROFILE\.ssh\id_rsa
   ```

2. If it doesn't exist, generate one:
   ```powershell
   ssh-keygen -t rsa -b 4096
   ```
   (Press Enter to accept defaults, or set a passphrase)

3. Copy public key to clipboard:
   ```powershell
   Get-Content $env:USERPROFILE\.ssh\id_rsa.pub | Set-Clipboard
   ```

4. SSH into your droplet and add it:
   ```bash
   ssh root@YOUR_DROPLET_IP
   mkdir -p ~/.ssh
   echo "PASTE_YOUR_KEY_HERE" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   chmod 700 ~/.ssh
   ```

### Config File Path Issues on Windows
If you're having trouble with the key file path, try:

1. Use forward slashes: `C:/Users/markl/.ssh/id_rsa` (not backslashes)
2. Use double backslashes: `C:\\Users\\markl\\.ssh\\id_rsa`
3. Use raw string format in the JSON (the example above should work)

### Still Having Issues?
1. Test SSH connection manually first:
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

2. If manual SSH works but the client doesn't:
   - Check the config file JSON is valid
   - Verify the key file path is correct
   - Make sure you're using the right username

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

