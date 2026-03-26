# ALPACA MEMORY BANK UPDATE PROPOSAL (Phase 3)

**Mission:** ALPACA MEMORY BANK DISCOVERY, RECONCILIATION, AND INSTITUTIONALIZATION  
**Phase:** 3 — Propose explicit diffs only. No wholesale rewrite.  
**Authority:** Cursor executor. Updates apply only after Phase 4 (CSA/SRE) approval.

---

## Diff 1 — Header version (OUTDATED)

- **Section:** Top of file (line 3).
- **Old text (verbatim):**
  `# Version: 2026-01-12 (SSH Deployment Verified)`
- **Proposed new text:**
  `# Version: 2026-01-12 (SSH Deployment Verified); Alpaca governance current 2026-03-17`
- **Reason:** Reconcile header with Alpaca governance scope (Tier 1/2/3, Telegram, E2E, etc.) without removing SSH verification date.
- **Evidence:** reports/audit/ALPACA_MEMORY_BANK_RECONCILIATION.md; MEMORY_BANK sections dated 2026-01-20 through 2026-03-17.

---

## Diff 2 — Log path env overrides (MISSING)

- **Section:** §5.5 EOD Data Pipeline (Canonical) — first paragraph after "Canonical 8-file bundle paths".
- **Old text (verbatim):**
  `Canonical 8-file bundle paths (relative to repo root; **do not move/rename**):`
  `- `logs/attribution.jsonl`, `logs/exit_attribution.jsonl`, `logs/master_trade_log.jsonl``
- **Proposed new text:** Insert after the three log paths:
  `Override (regression/isolation only): `EXIT_ATTRIBUTION_LOG_PATH`, `MASTER_TRADE_LOG_PATH` env vars; default = canonical paths.`
- **Reason:** Document env overrides used in exit_attribution.py and utils/master_trade_log.py so operators and audits know canonical can be overridden for tests.
- **Evidence:** src/exit/exit_attribution.py (OUT = Path(os.environ.get("EXIT_ATTRIBUTION_LOG_PATH", "logs/exit_attribution.jsonl"))); utils/master_trade_log.py (MASTER_TRADE_LOG = Path(os.environ.get("MASTER_TRADE_LOG_PATH", "logs/master_trade_log.jsonl"))).

---

## Diff 3 — Truth Gate (MISSING)

- **Section:** §3 GLOBAL RULES — add new subsection after 3.3 SAFETY RULES.
- **Old text (verbatim):**
  (End of §3.3 SAFETY RULES; next section is # 4. SIGNAL INTEGRITY CONTRACT)
- **Proposed new text:** Insert new subsection:
  `## 3.4 TRUTH GATE (ALPACA / DROPLET DATA)`
  `Cursor and all Alpaca actions MUST treat droplet execution and canonical data as the Truth Gate:`
  `- All reports and conclusions require droplet execution and canonical logs/state; no local-only conclusions.`
  `- Missing required data (e.g. exit_attribution, master_trade_log) = HARD FAILURE; do not proceed.`
  `- Join coverage below threshold (e.g. direction_readiness, exit-join health) = HARD FAILURE when asserted as readiness.`
  `- Schema mismatch or unversioned required fields = HARD FAILURE.`
  `- Only frozen artifacts (e.g. EOD bundle, frozen trade sets) may be used for learning or tuning.`
- **Reason:** Institutionalize Truth Gate as the named contract per mission; align with §0.1 and §3.2.
- **Evidence:** reports/audit/ALPACA_DISCOVERED_TRUTH.md (Governance / Truth Gate); mission Phase 6.

---

## Diff 4 — Project dir canonical (OUTDATED)

- **Section:** §6.3 SSH CONFIG — line "Canonical droplet: Prefer SSH alias **alpaca** ..."
- **Old text (verbatim):**
  `- **Canonical droplet:** Prefer SSH alias **alpaca** (use_ssh_config true); else `104.236.102.57`. Project dir `/root/stock-bot` or `/root/trading-bot-current` per deployment.`
- **Proposed new text:**
  `- **Canonical droplet:** Prefer SSH alias **alpaca** (use_ssh_config true); else `104.236.102.57`. Project dir **canonical:** `/root/stock-bot` (or `/root/stock-bot-current` if used as alternate; do not use `trading-bot-current` for stock-bot).`
- **Reason:** Single canonical project dir for stock-bot; avoid confusion with other bot path.
- **Evidence:** docs/ARCHITECTURE_AND_OPERATIONS.md; deploy_supervisor.py /root/stock-bot; scripts/diagnose_cron_and_git.py auto-detect.

---

## Diff 5 — Exit attribution schema version (MISSING, optional)

- **Section:** §7.12 v2 EXIT INTELLIGENCE LAYER — after "Output: `logs/exit_attribution.jsonl`".
- **Old text (verbatim):**
  `- **Exit attribution must be logged for every v2 exit**:`
  `  - Engine: `src/exit/exit_attribution.py``
  `  - Output: `logs/exit_attribution.jsonl``
- **Proposed new text:** Add one line:
  `  - Schema version: `ATTRIBUTION_SCHEMA_VERSION` in exit_attribution.py (e.g. 1.0.0).`
- **Reason:** Traceability to schema version for audits.
- **Evidence:** src/exit/exit_attribution.py ATTRIBUTION_SCHEMA_VERSION = "1.0.0".

---

## Diff 6 — Trade key builder (MISSING, optional)

- **Section:** §5 (Snapshot→Outcome Attribution) or §7.12 — join keys sentence.
- **Old text (verbatim):**
  `- **Join key precedence (deterministic exit joins):** `telemetry/snapshot_join_keys.py` — a) position_id (preferred); b) trade_id (live:SYMBOL:entry_ts); c) surrogate: symbol + side + entry_ts_bucket + intent_id.`
- **Proposed new text:** Append:
  ` For Alpaca, `trade_id` is built via `src/telemetry/alpaca_trade_key.build_trade_key(symbol, side, entry_ts)`.`
- **Reason:** Explicit reference for join and attribution audits.
- **Evidence:** src/exit/exit_attribution.py (build_trade_key); telemetry/snapshot_join_keys.py (trade_id precedence).

---

## Summary

| Diff | Section | Type | Required by reconciliation |
|------|---------|------|-----------------------------|
| 1 | Header | OUTDATED | Yes |
| 2 | §5.5 | MISSING | Yes |
| 3 | §3.4 Truth Gate | MISSING | Yes |
| 4 | §6.3 | OUTDATED | Yes |
| 5 | §7.12 | MISSING (optional) | No |
| 6 | §5 / §7.12 | MISSING (optional) | No |

Diffs 1–4 are recommended for approval. Diffs 5–6 are optional clarity; CSA/SRE may accept or defer.

---

*End of Phase 3. Pending Phase 4 CSA and SRE review (veto enabled).*
