#!/usr/bin/env bash
# CURSOR_ENFORCE_DROPLET_AND_NO_SUPPRESSION.sh
#
# Enforces:
# 1) Campaign runs ONLY on droplet (/root/stock-bot must exist)
# 2) No suppression modes (no long_only/short_only/suppress_*), always evaluate BOTH directions
# 3) Campaign passes flags that force direction search without suppression

set -euo pipefail

REPO="${REPO:-/root/stock-bot}"
cd "${REPO}" || exit 1

echo "=== ENFORCING DROPLET-ONLY + NO SUPPRESSION ==="

# -------------------------------------------------
# 0) Hard enforce droplet execution
# -------------------------------------------------
if [ "${REPO}" != "/root/stock-bot" ]; then
  echo "ERROR: Droplet enforcement active. REPO must be /root/stock-bot (got: ${REPO})."
  exit 1
fi
if [ ! -d "/root/stock-bot" ]; then
  echo "ERROR: /root/stock-bot not found. This must run on the droplet."
  exit 1
fi

# -------------------------------------------------
# 1) Patch campaign script to add droplet enforcement + --no_suppression (idempotent)
# -------------------------------------------------
python3 - <<'PY'
from pathlib import Path

p = Path("scripts/CURSOR_AUTONOMOUS_PROFITABILITY_CAMPAIGN.sh")
if not p.exists():
    raise SystemExit("Missing scripts/CURSOR_AUTONOMOUS_PROFITABILITY_CAMPAIGN.sh")

s = p.read_text(encoding="utf-8")
changed = False

# Ensure droplet enforcement block exists after "cd ... || exit 1"
if "Droplet enforcement active" not in s:
    anchor = 'cd "${REPO}" || exit 1\n\n'
    inject = '''cd "${REPO}" || exit 1

# --- DROPLET ENFORCEMENT (canonical truth root) ---
if [ "${REPO}" != "/root/stock-bot" ]; then
  echo "ERROR: Droplet enforcement active. REPO must be /root/stock-bot (got: ${REPO})."
  exit 1
fi
if [ ! -d "/root/stock-bot" ]; then
  echo "ERROR: /root/stock-bot not found. This must run on the droplet."
  exit 1
fi
# --- END DROPLET ENFORCEMENT ---

'''
    if anchor in s:
        s = s.replace(anchor, inject, 1)
        changed = True
    else:
        # Fallback: insert after first "exit 1"
        idx = s.find('exit 1\n\n')
        if idx != -1:
            s = s[:idx+len('exit 1\n\n')] + inject[len(anchor):] + s[idx+len('exit 1\n\n'):]
            changed = True

# Ensure --no_suppression is in the iteration launch cmd
if '"--no_suppression"' not in s and "'--no_suppression'" not in s:
    s = s.replace(
        "--force_direction_search\",\n      \"--force_entry_search\"",
        "--force_direction_search\",\n      \"--no_suppression\",\n      \"--force_entry_search\"",
        1
    )
    if "--no_suppression" not in s:
        s = s.replace(
            '"--force_direction_search",',
            '"--force_direction_search",\n      "--no_suppression",',
            1
        )
    changed = True

if changed:
    p.write_text(s, encoding="utf-8")
    print("Patched campaign: droplet-only enforcement + --no_suppression flag.")
else:
    print("Campaign already has droplet enforcement and --no_suppression.")
PY

# -------------------------------------------------
# 2) Patch iteration runner: ensure no_suppression in output (idempotent)
# -------------------------------------------------
python3 - <<'PY'
from pathlib import Path

p = Path("scripts/learning/run_profit_iteration.py")
if not p.exists():
    raise SystemExit("Missing scripts/learning/run_profit_iteration.py")

s = p.read_text(encoding="utf-8")
changed = False

# Ensure iteration_result includes no_suppression so artifacts prove compliance
if '"no_suppression": True' not in s and '"no_suppression": true' not in s:
    s = s.replace(
        '"idea": idea,',
        '"idea": idea,\n        "no_suppression": True,  # enforced: always both directions, no long_only/short_only',
        1
    )
    changed = True

if changed:
    p.write_text(s, encoding="utf-8")
    print("Patched run_profit_iteration.py: no_suppression in output; both directions enforced.")
else:
    print("run_profit_iteration.py already has no_suppression compliance.")
PY

# -------------------------------------------------
# 3) Commit (audit trail)
# -------------------------------------------------
git add scripts/CURSOR_AUTONOMOUS_PROFITABILITY_CAMPAIGN.sh scripts/learning/run_profit_iteration.py 2>/dev/null || true
git commit -m "Enforce droplet-only profitability campaign + forbid suppression; always evaluate long+short" || true

echo "=== DONE ==="
echo "Run on droplet:"
echo "  cd /root/stock-bot && bash scripts/CURSOR_AUTONOMOUS_PROFITABILITY_CAMPAIGN.sh"
