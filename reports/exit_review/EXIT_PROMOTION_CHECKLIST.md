# Exit pressure promotion checklist

All gates must pass before enabling EXIT_PRESSURE_ENABLED in production.

---

## G1 — Backtest improvement

- [ ] Backtest with EXIT_PRESSURE_ENABLED=1 vs baseline (same period).
- [ ] Objective function: giveback lower and/or saved_loss higher (within tail constraint).
- [ ] Document run dir and metrics in report.

---

## G2 — Tail loss

- [ ] Tail loss (e.g. 5th percentile P&L) does not increase beyond configured tolerance vs baseline.
- [ ] No material increase in max drawdown.

---

## G3 — Truth logs and dashboard

- [ ] logs/exit_truth.jsonl present and fresh (lines per day above threshold).
- [ ] Dashboard truth audit PASS for exit panels and exit truth coverage.
- [ ] No missing or stale exit_truth for any trading day.

---

## G4 — Integrity

- [ ] Attribution schema unchanged; exit_reason_code taxonomy respected.
- [ ] No regression in join (entry ↔ exit) or exit_attribution flow.

---

## G5 — Rollback validated

- [ ] Rollback plan documented: set EXIT_PRESSURE_ENABLED=0 (or omit); redeploy; confirm cascade behavior restored.
- [ ] Config patch (exit_tuning_patch.json) is applied only after Board approval; revert path documented.

---

## G6 — Shadow run

- [ ] Shadow run completed: exit pressure logged in parallel with current exits.
- [ ] Delta report: would-have-exited earlier/later counts; expected giveback/saved_loss deltas.
- [ ] Direction aligns with objective (e.g. more saved_loss, less giveback) before promotion.

---

## Sign-off

- [ ] SRE: Logs and EOD wiring verified.
- [ ] Quant: Objective and effectiveness v2 reviewed.
- [ ] Board: Promotion gates passed; rollback plan approved.

---

## Board review (exit tuning & promotion)

| Field | Value |
|-------|--------|
| **Review date** | *(YYYY-MM-DD)* |
| **Tuning recommendations** | ☐ Approved for application / ☐ Deferred / ☐ Rejected |
| **EXIT_PRESSURE_ENABLED promotion** | ☐ Approved / ☐ Not yet (gates incomplete) / ☐ Rejected |
| **Conditions / notes** | *(e.g. shadow 7d; paper only; tail loss cap)* |
| **Board sign-off** | *(name or role)* |
