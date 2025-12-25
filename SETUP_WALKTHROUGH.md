# Droplet Client Setup - Complete Walkthrough
## Your Droplet IP: 104.236.102.57

Follow these steps in order. All commands are ready to copy/paste.

---

## Step 1: Add Config File to .gitignore ✅ (Already Done)

This step is already complete! Your `.gitignore` already includes `droplet_config.json`.

---

## Step 2: Install the SSH Library

**On your LOCAL Windows machine (where Cursor is running), run:**

```bash
pip install paramiko==3.4.0
```

**Verify it worked:**
```bash
python -c "import paramiko; print('paramiko installed successfully')"
```

**Expected output:** `paramiko installed successfully`

---

## Step 3: Check for SSH Key (Choose Option A or B)

**First, check if you have an SSH key on your Windows machine:**

```powershell
Test-Path $env:USERPROFILE\.ssh\id_rsa
```

**If it returns `True`**, use **Option A** (SSH Key - More Secure)  
**If it returns `False`**, use **Option B** (Password - Simpler)

---

## Step 4A: Create Config File with SSH Key (If you have an SSH key)

**On your LOCAL Windows machine, create the config file:**

```bash
cat > droplet_config.json << 'EOF'
{
  "host": "104.236.102.57",
  "port": 22,
  "username": "root",
  "key_file": "C:/Users/markl/.ssh/id_rsa",
  "project_dir": "~/stock-bot"
}
EOF
```

**If your username is different from "markl", update the path:**
- Replace `C:/Users/markl/.ssh/id_rsa` with your actual path
- Common paths: `C:/Users/YOUR_USERNAME/.ssh/id_rsa`

**To find your exact path:**
```powershell
$env:USERPROFILE\.ssh\id_rsa
```

---

## Step 4B: Create Config File with Password (If you don't have an SSH key)

**On your LOCAL Windows machine, create the config file:**

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

**Note:** This uses your SSH config file (`~/.ssh/config`) with host alias `alpaca`. Make sure you have `alpaca` configured in your SSH config.

---

## Step 5: Test the Connection

**On your LOCAL Windows machine, test the connection:**

```bash
python droplet_client.py
```

**Expected output:**
```
Droplet Client - Testing Connection
============================================================
Connected to: 104.236.102.57
Status:
{
  "timestamp": "...",
  "host": "104.236.102.57",
  "service_status": "active",
  ...
}
```

**If you see connection errors:**
- Make sure your droplet is running and accessible
- Verify SSH key path is correct (if using Option A)
- Verify password is correct (if using Option B)
- Try manual SSH first: `ssh root@104.236.102.57`

---

## Step 6: Verify Everything Works

**Run the verification script:**

```bash
python verify_droplet_setup.py
```

**Expected output:**
```
============================================================
Droplet Client Setup Verification
============================================================

Step 1: Checking config file...
   ✅ Config file found
   → Host: 104.236.102.57
   → User: root
   → Auth: SSH Key (or Password)

Step 2: Checking paramiko installation...
   ✅ paramiko installed (version: 3.4.0)

Step 3: Checking .gitignore...
   ✅ droplet_config.json is in .gitignore

Step 4: Testing connection to droplet...
   ✅ Connected to 104.236.102.57
   ✅ Service status: active
   ✅ Git branch: main

============================================================
✅ All checks passed! Droplet client is ready to use.
```

---

## Step 7: Test Common Operations

**Test 1: Get Git Status**
```python
python -c "from droplet_client import get_droplet_git_status; import json; print(json.dumps(get_droplet_git_status(), indent=2))"
```

**Test 2: Get Recent Logs**
```python
python -c "from droplet_client import get_droplet_logs; logs = get_droplet_logs(10); print('\n'.join(logs[-10:]))"
```

**Test 3: Get Full Status**
```python
python -c "from droplet_client import get_droplet_status; import json; print(json.dumps(get_droplet_status(), indent=2))"
```

---

## Step 8: You're Done! 🎉

Now you can ask Cursor natural language questions like:

- "What's the status of the droplet?"
- "Show me the last 50 lines of logs"
- "What's the git status on the droplet?"
- "Deploy the latest changes"
- "Check if the bot is running"

Cursor will handle all the SSH connections and commands for you!

---

## Troubleshooting

### If Step 5 fails with "Authentication failed":
- **SSH Key:** Make sure the key file path is correct and the key is added to the droplet
- **Password:** Double-check the password in the config file
- Test manually: `ssh root@104.236.102.57`

### If Step 5 fails with "Connection timeout":
- Verify the droplet is running
- Check firewall allows SSH (port 22)
- Ping the droplet: `ping 104.236.102.57`

### If you need to set up SSH key:
1. Generate key: `ssh-keygen -t rsa -b 4096`
2. Copy public key: `type $env:USERPROFILE\.ssh\id_rsa.pub`
3. Add to droplet: SSH in and add to `~/.ssh/authorized_keys`

