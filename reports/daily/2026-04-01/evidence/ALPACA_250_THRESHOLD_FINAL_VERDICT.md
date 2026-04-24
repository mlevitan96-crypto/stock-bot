# ALPACA_250_THRESHOLD_FINAL_VERDICT

- **Has the system crossed 250 canonical trades (post-era, no floor)?** **YES**
- **Should the 250 milestone have fired (per notifier rules)?** **NO**
- **If YES and it did not fire — exact reason:** N/A (milestone should not have fired under current rules)
- **Why notifier has not fired (operator summary):** Ground truth >= 250, but `milestone_counting_basis` is **integrity_armed** and the session is **not armed** (arm_epoch unset until DATA_READY + coverage freshness + strict ARMED + exit tail probe pass). Notifier count stays **0** until then — independent of cumulative post-era closes.
- **Corrective action:** No strategy change. Let the integrity cycle run green to arm the day, or governance may set `milestone_counting_basis` to `session_open` (policy only). Check warehouse coverage / strict gate / exit_probe if arm never arms.
