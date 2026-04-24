# Comprehensive System Audit

**Role:** Principal Staff / Quant Data Engineering review  
**Scope:** Full repository architecture, configuration sprawl, and telemetry exhaust for ML readiness  
**Constraint:** Analysis and recommendations only — **no code changes** in this pass.

---

## Evidence: Gemini folder & droplet parity (2026-04-02)

| Artifact | Local workspace | Droplet (`ssh alpaca`, `/root/stock-bot`) |
|----------|-----------------|----------------------------------------|
| Extract script | `scripts/extract_gemini_telemetry.py` | Same path (deploy with code) |
| Output dir | `reports/Gemini/` | `reports/Gemini/` |
| Last **local** run | `python scripts/extract_gemini_telemetry.py` → **0 rows** (no recent JSONL in 48h window) | N/A |
| Last **droplet** run | Pulled via `scp alpaca:.../reports/Gemini/*` → see below | `python3 scripts/extract_gemini_telemetry.py` |

**Droplet-derived `telemetry_overview.md` (48h UTC window ending ~`2026-04-02T20:05:44Z`):**

| File | Rows |
|------|------|
| `entries_and_exits.csv` | 4187 |
| `blocked_and_rejected.csv` | 2954 |
| `shadow_and_ab_testing.csv` | 5373 |
| `signal_intelligence_spi.csv` | 17434 |

**Interpretation:** Local `reports/Gemini/` should be refreshed from the droplet when validating production-like telemetry; an empty local extract is **expected** if logs are not present under the repo’s `logs/` and `data/` for the window.

**Telegram:** Not emitted by `extract_gemini_telemetry.py`. Alerts live in separate services/scripts (e.g. `telemetry/alpaca_telegram_integrity/`, `scripts/alpaca_telegram.py`, systemd timers). There is **no** single CSV join between Telegram text and SPI rows in-repo.

---

# Phase 1: The Dead Code & Dependency Purge

## 1.1 Unused imports & variables (high-signal findings)

**Method:** Targeted `grep` on `main.py` and primary modules; full-repo unused-import analysis would require `ruff`/IDE (not run — `ruff` not installed in the active Python environment).

### `main.py` — likely unused imports from legacy composite

The following symbols are **imported** from `signals.uw_composite` but **never referenced** elsewhere in `main.py` (only the import line matches):

- `compute_uw_composite_score`
- `should_enter` (as `uw_should_enter`)
- `log_uw_attribution`
- `apply_sizing`

The live path uses **`uw_composite_v2`** (`import uw_composite_v2 as uw_v2`, `should_enter_v2`, `compute_composite_score_v2`, etc.).

**Recommendation:** Confirm with one full-symbol search, then remove or gate behind explicit legacy flags.

### Other patterns (repository-wide)

- **`_MISSING_REQUESTS_LIB` / `_MISSING_ALPACA_SDK` / `_MISSING_FLASK`:** Used for optional dependency stubs; not “dead” but increase surface area.
- **Multiple `datetime.utcnow()` deprecation warnings** in logs indicate technical debt, not unused code.

*Exhaustive F401 across 400+ Python files is out of scope for this document; recommend CI job: `ruff check --select F401,F841`.*

## 1.2 Orphaned functions / classes / files

| Area | Observation |
|------|-------------|
| **`signals/uw_composite.py`** | Legacy UW composite + `should_enter`; **not** on the `main.py` hot path for scoring (v2 engine is canonical). Still referenced by **`validation/validate_full_trade_flow.py`** and **archived** investigation scripts. |
| **`archive/`** | Large tree of historical scripts, docs, and one-off investigations — **not** imported by production `main.py`. Safe to treat as **non-runtime** (retain for archaeology or delete under a formal deprecation policy). |
| **`integrate_structural_intelligence.py`**, **`fix_uw_signal_parser.py`** | One-shot / migration-style scripts; not part of systemd `ExecStart`. |
| **Kraken-era scripts** (git status shows deletions) | Confirmed absent from Alpaca paper path per prior audits; any remaining references should be grep-cleaned in a follow-up PR. |

**Displacement / exit “orphans”:** Multiple **documented** exit mechanisms coexist in `main.py` (trailing %, fixed `stop_loss_pct`, `exit_score_v2`, optional `exit_pressure_v3`, stale trade, structural exit). All are **wired**, not orphaned — the issue is **overlap**, not dead code (see Phase 1.3).

## 1.3 Redundant logic

| Redundancy | Where | Risk |
|------------|-------|------|
| **Entry score floor** | `Config.MIN_EXEC_SCORE`, `config.registry.Thresholds.MIN_EXEC_SCORE`, systemd drop-in `MIN_EXEC_SCORE`, `uw_composite_v2.ENTRY_THRESHOLDS` + `get_threshold()` + env `ENTRY_THRESHOLD_BASE`, inline `getattr(Config, "MIN_EXEC_SCORE", 2.5)` / `3.0` in a few paths | Drift: different floors at different layers. |
| **Order / notional validation** | `submit_entry` (min notional, spread, short checks) + `risk_management.validate_order_size` + `trade_guard.evaluate_order` | Same order validated multiple times with slightly different rules. |
| **Logging sinks** | `log_event`, `jsonl_write`, `append_jsonl`, `TelemetryLogger`, `log_system_event`, dedicated files (`logs/worker_debug.log`, `gate_diagnostic.jsonl`, `run.jsonl`, etc.) | Duplicate narratives for one decision; harder ML feature alignment. |
| **Trailing stop semantics** | `Config.TRAILING_STOP_PCT` used in worker; **also** `main.py` ~8080 uses `Config.TRAILING_STOP_PCT / 100` as if it were **percent points** — if `TRAILING_STOP_PCT` is a **fraction** (e.g. `0.035`), this is **inconsistent** with the worker path | Silent behavioral bug risk; needs single definition of units. |
| **Stop-loss %** | Hardcoded `stop_loss_pct = -0.008` / `-0.01` in exit worker **vs** `src/exit/stops_v2.py` advisory stops **vs** `risk_management` limits | Three different “stop” concepts without one schema. |

---

# Phase 2: The “Single Source of Truth” Configuration Check

## 2.1 Configuration conflicts (trading thresholds & hold times)

**Representative duplicates:**

| Knob | Definition locations |
|------|----------------------|
| **Min entry / exec score** | `main.Config.MIN_EXEC_SCORE` (`get_env`), `config.registry.Thresholds.MIN_EXEC_SCORE`, **systemd** `Environment=MIN_EXEC_SCORE=…` (e.g. `paper-overlay.conf`), `uw_composite_v2.ENTRY_THRESHOLDS` + `get_threshold()` + **`ENTRY_THRESHOLD_BASE`** env, `should_enter_v2` comments referencing 3.0, scattered `getattr(Config, "MIN_EXEC_SCORE", …)` **fallback literals** (`2.5`, `3.0`) |
| **Trailing stop** | `Config.TRAILING_STOP_PCT`, `Thresholds.TRAILING_STOP_PCT`, worker inline acceleration (`0.005`), MIXED regime override (`0.01`), profit-target path uses `Config.PROFIT_TARGETS` / `SCALE_OUT_FRACTIONS` |
| **Displacement min hold** | `Config.DISPLACEMENT_MIN_HOLD_SECONDS`, `registry.Thresholds.DISPLACEMENT_MIN_HOLD_SECONDS`, `trading/displacement_policy.DISPLACEMENT_MIN_HOLD_SECONDS`, **`SHADOW_EXPERIMENTS`** inline overrides (`5*60`, `45*60`) |
| **Stop-loss (fixed %)** | **Inline** in `main.py` exit worker (`-0.008` / `-0.01`) — **not** env-driven |
| **Signal decay / hold floor** | `board.eod.exit_regimes`, `policy_variants` (`decay_ratio_threshold`, `min_hold_minutes_before_decay_exit`), `TIME_EXIT_MINUTES` env, `STALE_TRADE_*`, `FEATURE_B2_NO_EARLY_SIGNAL_DECAY_EXIT` |
| **V2 exit threshold** | `V2_EXIT_SCORE_THRESHOLD` env in worker (`_v2_exit_thr`) |
| **Paper / risk caps** | `risk_management.get_risk_limits()` hardcoded paper vs live dollars, `SIZE_BASE_USD` / `POSITION_SIZE_USD` / `max_position_dollar` |

**Conclusion:** There is **no** single source of truth today. Precedence is effectively: **systemd Environment > `.env` (via `EnvironmentFile`) > Python `get_env` defaults > inline constants**.

## 2.2 Environment variable mapping

**Loaders:**

- **`main.py`:** `load_dotenv` at repo root; class **`Config`** uses local **`get_env()`** wrapping `os.getenv` for **dozens** of trading, telemetry, and feature flags (lines ~345–591 and scattered later: `AUDIT_MODE`, `BAR_STALE_MAX_AGE_MINUTES`, `DECISION_LEDGER_CAPTURE`, etc.).
- **`config/registry.py`:** **`get_env` / `get_env_bool`** on **`Thresholds`**, **`APIConfig`**, and **`COMPOSITE_WEIGHTS_V2`** constants.
- **`uw_composite_v2.py`:** `os.environ.get` for **`DISABLE_ADAPTIVE_WEIGHTS`**, **`FLOW_WEIGHT_MULTIPLIER`**, **`UW_WEIGHT_MULTIPLIER`**, **`REGIME_WEIGHT_MULTIPLIER`**, **`ENTRY_THRESHOLD_BASE`**, **`V2_SHAPING_ENABLED`**, etc.
- **`config/tuning/tuning_loader.py`:** `GOVERNED_TUNING_CONFIG` or **`config/tuning/active.json`** for exit weights / optional entry overlays.
- **Scripts / telemetry:** Hundreds of additional `os.environ` / `getenv` reads (e.g. `EXIT_PRESSURE_ENABLED`, `PAPER_SECOND_CHANCE_DELAY_SECONDS`, truth router, Telegram integrity).

**Complete “every variable” table:** Not inlined here (100+ symbols). **Actionable approach:**

1. Run `rg 'get_env\\(|os\\.getenv|os\\.environ\\.get' --glob '*.py'` and dump to `docs/env_inventory.csv`.  
2. Classify each key as **trading**, **infra**, **telemetry**, **experimental**.  
3. Mark **authoritative** vs **deprecated**.

**`.env` file:** Documented as loaded by systemd `EnvironmentFile=/root/stock-bot/.env` for `stock-bot.service`. Variables **not** in `.env` may still be set via **`systemd` drop-ins** (observed: `MIN_EXEC_SCORE`, truth router, paper exec promo).

## 2.3 Consolidation plan (strict)

1. **Introduce one canonical `TradingRuntimeConfig`** (dataclass or pydantic model) built **once** at process start from:
   - optional JSON/YAML **`config/runtime_trading.yaml`** (versioned, committed),
   - then **environment overrides** (single documented prefix e.g. `STOCKBOT_`),
   - **no** duplicate defaults inside `main.py` **and** `registry.py` — one module **imports** the other.
2. **Remove threshold literals** from `uw_composite_v2` for entry execution; keep **scoring** thresholds separate from **execution** `MIN_EXEC_SCORE` or rename to `SCORING_ENTRY_THRESHOLD_*` to avoid confusion.
3. **Systemd / `.env`:** Either (a) **only** pass non-secret **paths** and **mode** flags, or (b) generate drop-ins from the same `runtime_trading.yaml` in deploy — **never** hand-edit `MIN_EXEC_SCORE` in three places.
4. **Unit policy:** Store **all** percentages as **fractions** (0.035) or **all** as **basis points**; add assertions in tests.
5. **Telemetry:** Emit a single **`config_snapshot.jsonl`** row at startup with resolved numeric config (redact secrets) for ML joins.
6. **Deprecation:** Mark `Thresholds` duplicates as re-exports from canonical config for one release, then delete.

---

# Phase 3: The Telemetry Hardening Check

## 3.1 Data completeness — SPI CSV, entries CSV, Telegram

### Active `WEIGHTS_V3` keys (core reset, seven components)

`options_flow`, `dark_pool`, `greeks_gamma`, `ftd_pressure`, `iv_term_skew`, `oi_change`, `toxicity_penalty`

### `signal_intelligence_spi.csv` — what is actually written

**Headers today** (`scripts/extract_gemini_telemetry.py` → `SPI_HEADERS`):

`timestamp_utc`, `source_file`, `symbol`, `total_score`, `freshness`, **`component_flow`**, **`component_dark_pool`**, **`component_greeks_gamma`**, **`component_ftd_pressure`**, **`component_squeeze_score`**, `decision`, `source_tag`

| WEIGHTS_V3 component | In SPI? | Notes |
|----------------------|---------|--------|
| `options_flow` | **Partial** | Mapped from composite key **`flow`** (or `options_flow` in some rows). |
| `dark_pool` | **Yes** | `component_dark_pool` |
| `greeks_gamma` | **Yes** | `component_greeks_gamma` |
| `ftd_pressure` | **Yes** | `component_ftd_pressure` |
| `iv_term_skew` (weight) | **No** | Scored as IV skew; **`components` dict key is `iv_skew`** (not `iv_term_skew`). SPI extract does **not** map `iv_skew` → column. |
| `oi_change` | **No** | Present in **`components`** as **`oi_change`** — **not extracted** to SPI CSV. |
| `toxicity_penalty` | **No** | Present in **`components`** as **`toxicity_penalty`** — **not extracted** to SPI CSV. |
| *Legacy* `squeeze_score` | **Yes** | **`component_squeeze_score`** still in CSV though **removed** from streamlined `WEIGHTS_V3` — **legacy exhaust**. |

**Answer to the audit question:** **No.** The seven active weights are **not** all explicitly present as columns. **Three** are missing from the SPI schema entirely; **one** legacy column (`squeeze_score`) remains.

### `entries_and_exits.csv`

**No per-ticker component breakdown.** Columns are execution-centric (symbol, side, qty, prices, PnL). **No** join key guaranteed to SPI except symbol + coarse timestamp (must be built in ETL).

### Telegram

**Out of band** for this extract. No guarantee that an alert contains all seven components unless templates are audited separately (`telemetry/alpaca_telegram_integrity`, governance scripts).

## 3.2 Missing links — where values drop or fail silently

| Stage | Risk |
|-------|------|
| **`uw_composite_v2._compute_composite_score_core`** | Returns a **wide** `components` dict (`flow`, `iv_skew`, `oi_change`, `toxicity_penalty`, `congress`, `etf_flow`, `squeeze_score`, …). Streamlined **`WEIGHTS_V3`** zeroes unused weights in `get_weight`, but **component values may still be computed** and emitted — ML consumers must filter by `component_sources` / version or slim the dict in a future refactor. |
| **Attribution / JSONL writers** | If `components` omitted or nested under `composite_meta`, extractors see `{}` → **empty** component columns. |
| **`extract_gemini_telemetry.py`** | **`component_get`** only looks up **fixed** names; **no** `iv_skew` / `oi_change` / `toxicity_penalty` mapping. |
| **`rows_emit_uw_intel`** | Sets **`component_greeks_gamma`**, **`ftd_pressure`**, **`squeeze_score`** to **empty strings** always — **guaranteed data loss** for those columns from `logs/uw_attribution.jsonl`. |
| **Broad `try/except Exception: continue`** in `main()` of extract script | Skips entire file on **any** error during per-file processing — **silent** row loss (no error row in CSV). |
| **JSON decode errors** in `iter_jsonl` | Line skipped — **silent** loss. |

## 3.3 Legacy exhaust

| Legacy signal | Still in SPI or extract? |
|---------------|---------------------------|
| **`squeeze_score`** | **Yes** — `component_squeeze_score` |
| **`congress`**, **`etf_flow`**, **`market_tide`**, etc. | **Not** separate SPI columns; may still appear inside **`extra`** blobs in other CSVs or raw JSONL if logged |
| **`uw_v3` / old version tags** | `source_tag` values e.g. `uw_v3` in sample rows — naming drift vs current `V2` composite |

**Recommendation:** Align SPI headers with **exact** `components` keys emitted by `uw_composite_v2` + ML feature contract; drop `component_squeeze_score` if engine no longer uses it, **or** rename to `legacy_squeeze_score` until backfills complete.

---

## Appendix A — Files to touch in a follow-up “purge / SSOT / telemetry” PR (reference only)

- `main.py` (Config, exit worker % units, remove unused imports)  
- `config/registry.py` (dedupe vs Config)  
- `uw_composite_v2.py` (threshold naming vs execution gate)  
- `scripts/extract_gemini_telemetry.py` (SPI schema + error accounting)  
- `systemd` drop-ins / deploy docs (single env story)  
- `signals/uw_composite.py` (deprecate or quarantine)

---

## Appendix B — Droplet command cheat sheet (operations)

```bash
ssh alpaca 'cd /root/stock-bot && python3 scripts/extract_gemini_telemetry.py'
# Pull Gemini folder to laptop:
scp alpaca:/root/stock-bot/reports/Gemini/* ./reports/Gemini/
```

---

*End of audit document.*
