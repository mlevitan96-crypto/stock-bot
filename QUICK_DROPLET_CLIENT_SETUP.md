# Quick Droplet Client Setup

## What You Need

1. Your droplet IP address
2. SSH access (either SSH key or password)
3. Python with pip

## Setup Steps (5 minutes)

### Step 1: Install paramiko (SSH library)

```bash
pip install paramiko==3.4.0
```

**Verify:**
```bash
python -c "import paramiko; print('OK')"
```

### Step 2: Add to .gitignore (if not already)

```bash
echo "droplet_config.json" >> .gitignore
```

### Step 3: Create droplet_config.json

**Option A: Using SSH Key (Recommended)**

Create `droplet_config.json` in the project root:

```json
{
  "host": "YOUR_DROPLET_IP_HERE",
  "port": 22,
  "username": "root",
  "key_file": "C:/Users/markl/.ssh/id_rsa",
  "project_dir": "~/stock-bot"
}
```

**Replace:**
- `YOUR_DROPLET_IP_HERE` with your droplet's IP address
- `C:/Users/markl/.ssh/id_rsa` with your SSH key path (if different)

**Option B: Using Password**

```json
{
  "host": "YOUR_DROPLET_IP_HERE",
  "port": 22,
  "username": "root",
  "password": "YOUR_PASSWORD_HERE",
  "project_dir": "~/stock-bot"
}
```

### Step 4: Find Your SSH Key (If Using Option A)

**On Windows (PowerShell):**
```powershell
Test-Path $env:USERPROFILE\.ssh\id_rsa
```

If `True`, your key is at: `C:/Users/markl/.ssh/id_rsa` (replace `markl` with your username)

**If you don't have an SSH key:**
```powershell
ssh-keygen -t rsa -b 4096
```

Then copy your public key to the droplet:
```powershell
type $env:USERPROFILE\.ssh\id_rsa.pub
```

Copy the output and add it to your droplet's `~/.ssh/authorized_keys` file.

### Step 5: Test Connection

```bash
python droplet_client.py
```

You should see connection status and droplet information.

## Once Setup Complete

You can now use:
- `python EXECUTE_DROPLET_DEPLOYMENT_NOW.py` - Complete automated deployment
- Cursor will automatically use the droplet client for all deployments

## Full Documentation

See `SETUP_DROPLET_CLIENT.md` for detailed instructions and troubleshooting.

