# Board edge review — summary (template)

**Cohort:** Strict-scope live trades, `open_ts_epoch` = ______  
**Gate snapshot:** `LEARNING_STATUS` = ______ | `trades_seen` = ______ | `trades_complete` = ______  
**Cohort export:** `reports/ALPACA_STRICT_QUANT_EDGE_COHORT.json` (hash / mtime) ______  
**Exclusions:** Integrity weighting and warehouse truth excluded as certifying authority until **DATA_READY = YES** — **YES / NO** (must be YES for this packet)

**Board rules (from framework):** Three WHYs to mechanism; every material slide has **root cause**, **proposed action**, **confidence**; no metric without **HOW** (kill / gate / flip / size / delay entry / change exit / noise / telemetry gap).

---

## 1. Executive decision

| # | Decision | Classification (KEEP/KILL/GATE/SIZE) | Confidence |
|---|----------|----------------------------------------|------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

---

## 2. Top five profit levers (mechanism + fragility)

| Lever | Mechanism (WHY) | Fragile? | Scale? |
|-------|-----------------|----------|--------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

---

## 3. Top five loss leaks (root cause + HOW)

| Leak | WHY ×3 summary | HOW (lever) | Owner |
|------|----------------|-------------|-------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

---

## 4. Directional truth (long vs short)

| Side | Win rate | Expectancy | Tail (worst decile) | Counterfactual flip note |
|------|----------|------------|---------------------|--------------------------|
| Long | | | | Model-only |
| Short | | | | Model-only |

**Board question:** Is one side structurally wrong? **YES / NO** — evidence row: ______

---

## 5. Entry vs exit diagnosis

| Quadrant | Count | PnL | Verdict (entry vs exit problem) |
|----------|-------|-----|----------------------------------|
| Good entry / good exit | | | |
| Good entry / bad exit | | | |
| Bad entry / good exit | | | |
| Bad entry / bad exit | | | |

---

## 6. Exit taxonomy pressure

| Exit type | n | PnL | Giveback / tail note |
|-----------|---|-----|----------------------|
| Profit taking | | | |
| Stop / risk | | | |
| Time-based | | | |
| Defensive / forced | | | |
| Error / guardrail | | | |

---

## 7. Blocked & missed opportunity (strict-log view)

| Metric | Value | Interpretation (hypothesis level) |
|--------|-------|-----------------------------------|
| Blocked trades (count) | | |
| Estimated opportunity $ | | **If** warehouse-dependent, mark **provisional** |

---

## 8. Open questions & telemetry gaps

| Gap | Blocks which view? | Proposed telemetry |
|-----|-------------------|-------------------|
| | | |

---

## 9. Board alignment checklist

- [ ] Every slide has **root cause + action + confidence**  
- [ ] No chart without **HOW**  
- [ ] Strict cohort count reconciled to gate  
- [ ] Success pockets reviewed for fragility  
