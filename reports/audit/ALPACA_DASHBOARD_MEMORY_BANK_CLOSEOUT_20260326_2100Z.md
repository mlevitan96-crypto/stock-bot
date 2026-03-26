# Alpaca dashboard — Memory Bank canonicalization (closeout)

Memory Bank (`MEMORY_BANK.md`) now includes **Alpaca Dashboard — Canonical verification and recovery** with:

- **systemd unit:** `stock-bot-dashboard.service`
- **Verifier:** `scripts/dashboard_verify_all_tabs.py` and pass condition (exit 0, all tabs HTTP 200; currently 23/23)
- **Canonical endpoints:** `/api/alpaca_operational_activity?hours=72` (CSA disclaimer requirement); `/api/telemetry/latest/computed?name=data_integrity` (HTTP 200; `ok: false` → PARTIAL)
- **Proof locations:** `reports/audit/ALPACA_DASHBOARD_DROPLET_PROOF_<TS>.md`, `reports/ALPACA_DASHBOARD_VERIFY_ALL_TABS_<TS>.json`, `executed: true` for CSA
- **Recovery:** `git fetch` + `git reset --hard origin/main`, restart unit, re-run verifier; fix in repo only (no SCP)
- **Permanentizing commit:** `1bab716d51aca0373878612b1f66d20ccb53639f`
- **Authoritative artifacts:** pointers only (droplet proof, UI closeout, permanentize closeout)

CSA_VERDICT: MEMORY_BANK_CANONICALIZED
