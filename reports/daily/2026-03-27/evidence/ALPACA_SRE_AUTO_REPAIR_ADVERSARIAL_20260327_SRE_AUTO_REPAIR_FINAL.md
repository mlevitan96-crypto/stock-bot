# Adversarial review — SRE auto-repair engine

**Timestamp:** `20260327_SRE_AUTO_REPAIR_FINAL`

| Claim | Attack | Response |
|-------|--------|----------|
| Misclassification | Reasons mapped to wrong playbook | Precedence is explicit in `alpaca_sre_repair_playbooks.py`; escalate reasons force UNKNOWN before join-key mapping. |
| Destructive repair | Sidecar corrupts primary | `apply_backfill_for_trade_ids` only appends `strict_backfill_*` JSONL; primary logs unchanged. |
| Silent novel issues | UNKNOWN merged into MISSING_* | UNKNOWN skips `apply_backfill`; `immediate_unknown_escalation` when no known trade; incident JSON includes `sre_classification_sample`. |
| Non-deterministic | Random timestamps | Builder uses deterministic ISO from `trade_id` and exit row; same inputs → same lines. |
| Masking partial failure | Exit 0 with hidden incompletes | Exit 0 only when `final_gate.trades_incomplete == 0`; exit 2 persists with full gate snapshot in run JSON. |
