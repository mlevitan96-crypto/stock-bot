# Ethos violation

**Generated (UTC):** 2026-03-04T23:27:35.954250+00:00

Deployment via SSH alias `alpaca` is REQUIRED. The following assertions failed:

- droplet_config.json must have "host": "alpaca"; got '104.236.102.57'.

## Required

1. Ensure SSH alias **alpaca** is defined (e.g. in `~/.ssh/config`) and resolves to stock-bot droplet 104.236.102.57.
2. Create or update **droplet_config.json** in repo root with: `"host": "alpaca"` and `"use_ssh_config": true`.
3. Do not use raw IP in config when ethos requires alpaca.
