# CSA Mission: CSA_AUTOMATION_HEALTH_CHECK — Summary

**Mission ID:** CSA_AUTOMATION_HEALTH_CHECK  
**Run (UTC):** 2026-03-06T00:15:28  
**Verdict:** PROCEED (MED confidence)

---

## 1. What CSA is currently configured to ingest

| Source | How CSA ingests it | Trigger / when loaded |
|--------|--------------------|------------------------|
| **reports/audit/GOVERNANCE_AUTOMATION_STATUS.json** | Via `scripts/audit/csa_automation_evidence.py` → `load_automation_evidence(base)`. Loaded on every run. | Always (no CLI flag). Path is fixed: `reports/audit/GOVERNANCE_AUTOMATION_STATUS.json`. |
| **reports/board/WEEKLY_GOVERNANCE_SUMMARY_*.md** | Via same module → `load_recent_weekly_summaries(base)`. Up to 3 most recent files; path, date, and first 500 chars (preview) only. | Always when automation evidence is loaded. |
| **reports/audit/SRE_STATUS.json** | Via `_gather_context()` → `_load_json(base / "reports" / "audit" / "SRE_STATUS.json")`. Overridable with `--sre-status-json`. | Always (default path) or when `--sre-status-json` is set. |
| **reports/audit/SRE_EVENTS.jsonl** | Via `_gather_context()` → `_load_sre_events()`. Last up to 100 events (tail). Overridable with `--sre-events-jsonl`. | Always (default path) or when `--sre-events-jsonl` is set. |
| **reports/audit/** (file list only) | Via `_gather_context()`: list of filenames in `reports/audit` with suffix `.json` or `.md` → `ctx["audit_files"]`. **Content of AUTOMATION_TEST_REPORT_*.md is not parsed.** | Always. Used for “missing data” (e.g. “No audit artifacts found” if list empty). |
| **reports/board/** (file list only) | Via `_gather_context()`: list of filenames in `reports/board` with suffix `.json` or `.md` → `ctx["board_files"]`. | Always. |
| **Board review JSON** | Via `_gather_context()` → `_load_json(p)` when `--board-review-json` is provided. Full content loaded. | When CLI arg `--board-review-json` is passed (e.g. `reports/board/last387_comprehensive_review.json`). |
| **Shadow comparison JSON** | Via `_gather_context()` → `_load_json(p)` when `--shadow-comparison-json` is provided. Full content loaded. | When CLI arg `--shadow-comparison-json` is passed (e.g. `reports/board/SHADOW_COMPARISON_LAST387.json`). |
| **state/shadow/** (file list only) | Via `_gather_context()`: list of `.json` filenames in `state/shadow` → `ctx["shadow_files"]`. | Always. |
| **Context JSON** | Via `_gather_context()` when `--context-json` is provided. | When CLI arg `--context-json` is passed. |
| **Baseline snapshot** | Via `_gather_context()` when `--baseline-snapshot` is provided. | When CLI arg `--baseline-snapshot` is passed. |

**Not ingested as content:** CSA does **not** read the body of `reports/audit/AUTOMATION_TEST_REPORT_*.md` or other audit Markdown files; it only knows that such files exist (via `audit_files`). Any “ingest” of automation test reports is therefore **by presence only**, not by parsing.

---

## 2. What triggers a CSA run

- **Invocation:** `python scripts/audit/run_chief_strategy_auditor.py --mission-id <id> [options] --base-dir .`
- **Required:** `--mission-id` (e.g. `CSA_AUTOMATION_HEALTH_CHECK`).
- **Optional:**  
  `--board-review-json`, `--shadow-comparison-json`, `--context-json`, `--baseline-snapshot`, `--sre-status-json`, `--sre-events-jsonl`, `--base-dir`.
- **Who calls it:** Mission runners (e.g. deploy, C1/A3, B2 enable, integration verify scripts) invoke CSA before or after their steps; no automatic trigger (no cron). Triggers are **script/caller-driven**.

---

## 3. What CSA can detect (confirmed by this run)

| Capability | Where it appears | This run |
|------------|------------------|----------|
| **Automation evidence** | `payload["automation_evidence"]` in verdict JSON; “## Automation Evidence” in findings MD. | `governance_status: "ok"`, `governance_timestamp`, `anomalies: []`, `unavailable_reason: null`. |
| **Governance heartbeat** | From GOVERNANCE_AUTOMATION_STATUS.json via automation evidence module. | Last run 2026-03-05T23:59:46Z; status ok. |
| **anomalies_detected** | Derived in evidence as `governance_status == "anomalies"` and `anomalies` list. | `anomalies: []`, status ok. |
| **Promotable signals** | Verdict logic: board_review + shadow_comparison + low missing_data → PROCEED. | PROCEED (MED) with board + shadow provided; one missing_data item (board lacks exits_in_scope/opportunity_cost_ranked_reasons). |
| **SRE status** | `ctx["sre_status"]`, `sre_interpretation` in verdict. | overall_status OK, 0 events, no blocks. |

---

## 4. What CSA produces (confirmed by this run)

| Artifact | Path | Produced |
|----------|------|----------|
| **CSA verdict (JSON)** | `reports/audit/CSA_VERDICT_<mission-id>.json` | Yes — `CSA_VERDICT_CSA_AUTOMATION_HEALTH_CHECK.json` |
| **Board-grade Markdown (findings)** | `reports/audit/CSA_FINDINGS_<mission-id>.md` | Yes — `CSA_FINDINGS_CSA_AUTOMATION_HEALTH_CHECK.md` |
| **Latest summary (for Cursor block)** | `reports/audit/CSA_SUMMARY_LATEST.md`, `reports/audit/CSA_VERDICT_LATEST.json` | Yes — overwritten with this run |

---

## 5. Scope confirmation (CSA_AUTOMATION_HEALTH_CHECK)

- **GOVERNANCE_AUTOMATION_STATUS.json:** Ingested; automation_evidence in verdict shows governance_status, timestamp, anomalies.
- **AUTOMATION_TEST_REPORT_*.md:** Only presence in `audit_files` list; content not parsed.
- **SRE_STATUS.json:** Ingested; SRE status OK, event count 0, used in sre_interpretation.
- **CSA_VERDICT_*.json:** Not ingested by CSA (CSA produces them; other tools or humans read them).
- **Shadow/paper/live artifacts:** Board and shadow JSONs ingested when passed via `--board-review-json` and `--shadow-comparison-json`; `state/shadow` file list always gathered.

---

## 6. Command used for this run

```bash
python scripts/audit/run_chief_strategy_auditor.py \
  --mission-id CSA_AUTOMATION_HEALTH_CHECK \
  --board-review-json reports/board/last387_comprehensive_review.json \
  --shadow-comparison-json reports/board/SHADOW_COMPARISON_LAST387.json \
  --base-dir .
```

---

*No repo logic or automation definitions were modified. This summary describes CSA’s current configuration and behavior.*
