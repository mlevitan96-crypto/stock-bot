# SSH Configuration Setup - One-Time Setup

## Current Status
✅ **Memory Bank Updated**: Complete workflow with SSH details documented  
⚠️ **SSH Configuration**: Not yet configured (one-time setup needed)

## What This Means

**Once SSH is configured, I will:**
- ✅ Handle ALL changes automatically (no questions, no copy/paste)
- ✅ Connect to droplet via SSH automatically
- ✅ Check droplet status and come back with complete information
- ✅ Deploy changes and verify results automatically
- ✅ Complete the full workflow: User → Cursor → Git → Droplet → Git → Cursor → User

**Without SSH configuration, I will:**
- ✅ Still push all changes to Git automatically
- ✅ Still complete all local work
- ⚠️ Need you to trigger `git pull` on droplet once (post-merge hook handles the rest)
- ⚠️ Pull results from Git after you trigger the pull

## One-Time Setup Required

To enable full automation, I need you to provide SSH credentials **once**. I'll create the `droplet_config.json` file securely.

### Option 1: Provide Credentials (I'll create the file)
Just tell me:
- Droplet IP address or hostname
- Username (usually "root")
- Either:
  - Password, OR
  - Path to your SSH private key file

I'll create `droplet_config.json` and add it to `.gitignore` so it's never committed to Git.

### Option 2: You Create It Manually
Create `droplet_config.json` in the project root with:
```json
{
  "host": "your-droplet-ip",
  "port": 22,
  "username": "root",
  "password": "your-password",
  "project_dir": "~/stock-bot"
}
```

Or with SSH key:
```json
{
  "host": "your-droplet-ip",
  "port": 22,
  "username": "root",
  "key_file": "/path/to/your/private/key",
  "project_dir": "~/stock-bot"
}
```

## After Setup

Once `droplet_config.json` exists:
- ✅ I'll automatically connect via SSH for every task
- ✅ No more questions about how to proceed
- ✅ No more copy/paste requirements
- ✅ Complete automation end-to-end

## Security Note

`droplet_config.json` will be:
- ✅ Added to `.gitignore` (never committed to Git)
- ✅ Stored locally only
- ✅ Used only for SSH connections
- ✅ Never shared or exposed

---

**Ready to set up?** Just provide your droplet credentials and I'll configure everything automatically.

