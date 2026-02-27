# Droplet SSH connectivity

**For Cursor / scripts:** Prefer the **alpaca** SSH alias (`"host": "alpaca"`, `"use_ssh_config": true` in `droplet_config.json`). Alternative: direct IP `104.236.102.57` with `use_ssh_config: false` and `key_file`. See MEMORY_BANK §6.3 and `droplet_config.example.json`.

## Why "SSH unreachable" happened

The client was using a **10-second connect timeout** and **no retries**. On slow or busy networks, or when the droplet was briefly busy, the first attempt could time out and raise:

`NoValidConnectionsError: [Errno None] Unable to connect to port 22 on <host>`

Paramiko’s `Errno None` means it’s an aggregate of one or more failed connection attempts (e.g. socket timeout, connection refused). The real cause was not clearly reported.

## What was fixed (in code)

1. **`droplet_client.py`**
   - **Connect timeout** increased from 10s to **30s** (configurable via `connect_timeout` in `droplet_config.json` or env `DROPLET_CONNECT_TIMEOUT`).
   - **Retries**: **5 attempts** with backoff (configurable via `connect_retries` or `DROPLET_CONNECT_RETRIES`).
   - **Error reporting**: On failure, the client now surfaces **underlying errors** from Paramiko’s `NoValidConnectionsError.errors` and suggests causes (droplet off, firewall, timeout, etc.).
   - **Timeouts**: `banner_timeout` and `auth_timeout` are set to the same value as `timeout` so slow SSH handshakes don’t fail early.

2. **Diagnostic script**
   - `scripts/diagnose_droplet_ssh.py`: run locally to test SSH and print the exact error if connection fails.

## Your config

**Preferred:** Use the **alpaca** SSH alias so host, port, and key come from `~/.ssh/config`:

- In `droplet_config.json`: `"host": "alpaca"`, `"use_ssh_config": true`
- In `~/.ssh/config`: a `Host alpaca` block with `HostName 104.236.102.57`, `User root`, and `IdentityFile` (or let the client use your default key)

**Alternative:** Use the IP directly:

- `"host": "104.236.102.57"`, `"use_ssh_config": false`, and `"key_file": "C:/Users/markl/.ssh/id_ed25519"` (or your key path)

Optional (defaults in code):

- `"connect_timeout": 30` — increase to 60 if your network is slow.
- `"connect_retries": 5` — increase if you see transient failures.

## If SSH still fails

1. Run: `python scripts/diagnose_droplet_ssh.py` and check the printed error and “Underlying errors”.
2. From a terminal: `ssh -v alpaca` (preferred) or `ssh -v root@104.236.102.57` to see where it fails.
3. Confirm the droplet is on and that port 22 is open (DigitalOcean firewall / security groups).
4. If timeouts persist, set `connect_timeout` to 60 (or higher) in `droplet_config.json`.
