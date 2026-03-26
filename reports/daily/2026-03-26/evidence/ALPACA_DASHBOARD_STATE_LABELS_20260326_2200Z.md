# Alpaca dashboard — STALE / PARTIAL labeling

**Timestamp:** 20260326_2200Z  

## Mechanism

- **`window.setTabStateLine(tabKey, state, detail)`** updates `#tab-state-line-<tabKey>`.  
- **`window.tabStateFromApi(iso, staleHours, partialMsg)`** compares server ISO timestamp age to thresholds.  
- States: **`ok`**, **`stale`**, **`partial`**, **`disabled`** (CSS: `.tab-state-banner.*`).

## Per-tab freshness / semantics

| Tab | STALE rule | PARTIAL / other |
|-----|------------|-----------------|
| `positions` | (no clock on API) | Auth / broker errors → PARTIAL; zero positions → OK with explanation |
| `closed_trades` | `response_generated_at_utc` &gt; **72h** | Auth failure, missing timestamp |
| `system_health` | `generated_at_utc` &gt; **48h** | Empty integrity payload, load failure |
| `executive` | (no auto stale in minimal loader) | Auth failure → PARTIAL |
| `sre` | (no auto stale) | Auth failure → PARTIAL; “Critical” card restyled informational |
| `signal_review` | (no clock) | Empty log → PARTIAL with explanation |
| `failure_points` | (no clock) | Auth / load errors → PARTIAL |
| `telemetry` | `idx.as_of_ts` &gt; **168h** | Index `error`, missing `as_of_ts`, partial computed artifacts (amber **PARTIAL TELEMETRY** banner inside tab), fetch failures |
| `learning_readiness` | (varies by backend) | Success still labeled **PARTIAL** at tab strip: “NOT CSA certification” |
| `profitability_learning` | (no clock) | No cockpit file, auth, errors |
| `fast_lane` | Last `timestamp_completed` &gt; **168h** | No cycles / no timestamps, auth, errors |

## Operational activity panel

- Separate from tabs: API returns `state` **OK** / **PARTIAL** / **DISABLED** with explicit `orders_log` reasons; not merged into tab strip keys.

## Principle

- **PARTIAL** and **STALE** describe **data visibility and age**, not “trading failed.”  
- No red “failure” styling for accepted learning/telemetry gaps.
