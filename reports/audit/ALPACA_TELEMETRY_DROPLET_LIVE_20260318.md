# Alpaca telemetry / supervisor fix — live on droplet

**UTC:** 2026-03-18 (deploy via `DropletClient`)

| Check | Result |
|-------|--------|
| **Path** | `/root/stock-bot` |
| **After `git reset --hard origin/main`** | `a26061d` — fix(supervisor): protect telemetry jsonl from startup truncation; proof writes PENDING result |
| **`HEAD` vs `origin/main`** | Match |
| **`systemctl restart stock-bot`** | OK |
| **`systemctl is-active stock-bot`** | `active` |

**Commit on droplet:** `a26061da492b996e83b8fd527d153244a5030945`

GitHub `main` was already at this commit; droplet advanced from `c9f836a` → `a26061d` on fetch/reset.
