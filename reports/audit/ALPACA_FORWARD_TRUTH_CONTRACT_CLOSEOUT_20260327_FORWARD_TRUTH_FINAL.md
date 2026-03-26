# CSA stop-gate — forward truth contract

**Timestamp:** `20260327_FORWARD_TRUTH_FINAL`

## Checklist

| Item | Met |
|------|-----|
| Scheduled job produces artifacts | Yes — systemd timer every 15m; per-run JSON + MD under `reports/` and `reports/audit/` |
| Incomplete → bounded repair + re-gate | Yes — runner loops ≤6 repair iterations with sleep and re-evaluates `evaluate_completeness` |
| Persist incomplete → INCIDENT | Yes — exit **2**, `--incident-json` / `--incident-md` populated |
| Incomplete zero → CERT_OK | Yes — exit **0**, run JSON + MD; manual proof `manual_exit_code: 0` |
| Exit semantics | 0 = OK, 2 = incident, 1 = precheck/structural/timeout |

## CSA verdict line

**CSA_VERDICT: FORWARD_TRUTH_CONTRACT_ACTIVE**

Evidence: `reports/audit/ALPACA_FORWARD_TRUTH_CONTRACT_DROPLET_BUNDLE_20260327_FORWARD_TRUTH_FINAL.json`, timer/service `systemctl` excerpts, `latest_run_json_head` with `trades_incomplete: 0`, journal excerpt.
