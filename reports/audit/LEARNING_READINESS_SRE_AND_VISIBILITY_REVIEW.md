# Learning & Readiness — SRE/Eng and Customer Visibility Review

**Purpose:** SRE/Eng leader and customer advocate checklist so the Learning tab and trade-review visibility are verified and pushed for operator visibility.

---

## SRE / Eng leader review

- [ ] **Learning tab loads:** More → Learning & Readiness renders without blank or "Failed to load". If it does not load, check: `/api/learning_readiness` returns 200 and JSON with `telemetry_trades`, `visibility_matrix`; dashboard logs for Python errors; browser console for fetch/parse errors.
- [ ] **API always returns 200:** `/api/learning_readiness` must not 500. All exceptions are caught and a safe payload is returned so the tab can at least show an error message.
- [ ] **Cron keeps counts fresh:** `scripts/governance/check_direction_readiness_and_run.py` runs every 5 min (9–21 UTC, Mon–Fri). Check `logs/direction_readiness_cron.log` and `state/direction_readiness.json` mtime.
- [ ] **Visibility matrix is computed:** API reads last 200 lines of `logs/exit_attribution.jsonl` and returns `visibility_matrix` (feature × count × pct). Tab renders it as a table.

---

## Customer advocate — push for visibility

- [ ] **Operator can see "Are we still reviewing?"** — Tab shows "Still reviewing? Yes." and explains that counts and matrix are updated every 5 min.
- [ ] **Operator can see "Close to promotion?"** — Tab shows what is missing for replay (e.g. "Need N more telemetry-backed exits", "Need 90% telemetry coverage").
- [ ] **Operator can see "Do we keep looking after 100?"** — Tab shows "Review continues after 100" copy and the visibility matrix over the last 200 exits.
- [ ] **Single place for learning state:** All of: trades reviewed, visibility matrix, promotion readiness, replay status, what "Wait" means, update schedule — are in one tab (Learning & Readiness). No separate banners.

---

## Adversarial — are we looking at all things?

- [ ] **Exit attribution is the source of truth:** Learning counts and matrix come from `logs/exit_attribution.jsonl` only. No shadow or legacy path should be used for "trades reviewed."
- [ ] **Matrix covers required fields:** Visibility matrix includes: `intel_snapshot_entry`, `intel_snapshot_exit`, `direction`, `side`, `position_side`, `symbol`, `sizing`. If a field is missing from the matrix, add it so we are "looking at all things."
- [ ] **Cron uses same definition as API:** `direction_readiness.py` counts a record as telemetry-backed iff `direction_intel_embed.intel_snapshot_entry` is a non-empty dict. The matrix uses the same logic for `intel_snapshot_entry` / `intel_snapshot_exit`.
- [ ] **No silent pass:** If the API fails, the tab shows an error message (and optionally the `error` field from the payload). No blank screen without explanation.

---

*Ref: dashboard.py (api_learning_readiness, loadLearningReadiness), src/governance/direction_readiness.py, scripts/governance/check_direction_readiness_and_run.py.*
