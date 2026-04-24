## Suppression / blockers

- **config.enabled:** True
- **TELEGRAM_GOVERNANCE_INTEGRITY_ONLY:** `(unset)`
- **Duplicate-send guard:** `fired_milestone` for current `session_anchor_et` = **False**
- **Integrity not armed (basis=integrity_armed):** True → milestone count forced to **0** until armed

### Milestone vs 100-trade checkpoint
- **250 milestone** does **not** use the same DATA_READY / strict ARMED gate as the 100-trade checkpoint; it keys off `unique_closed_trades >= target` and `not fired_milestone` for the ET session anchor.

### If ground truth >= 250 but notifier < 250 (class C)
- Primary cause: **count floor** (`session_open` or `integrity_armed` epoch) excludes closes before the floor while post-era cumulative count includes them.

### Trade #250 row (era / key)
- Row used for #250 identity is from first close per key; verify `trade_id` present: `True`
