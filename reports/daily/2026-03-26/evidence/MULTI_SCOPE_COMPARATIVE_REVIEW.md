# Multi-scope comparative review

**Generated (UTC):** 2026-03-04T23:31:39.116832+00:00

## Learning & telemetry by scope

- **7d:** telemetry_backed=387, ready_for_replay=False
- **14d:** telemetry_backed=387, ready_for_replay=False
- **30d:** telemetry_backed=387, ready_for_replay=False
- **last100:** telemetry_backed=100, ready_for_replay=True
- **last387:** telemetry_backed=387, ready_for_replay=True
- **last750:** telemetry_backed=387, ready_for_replay=False

## PnL by scope

- **7d:** total_pnl_attribution_usd=-136.47, total_exits=2000, win_rate=0.2015
- **14d:** total_pnl_attribution_usd=-136.47, total_exits=2000, win_rate=0.2015
- **30d:** total_pnl_attribution_usd=-136.47, total_exits=2000, win_rate=0.2015
- **last100:** total_pnl_attribution_usd=-18.59, total_exits=100, win_rate=0.1952
- **last387:** total_pnl_attribution_usd=-30.3, total_exits=387, win_rate=0.2081
- **last750:** total_pnl_attribution_usd=-123.89, total_exits=750, win_rate=0.1972

## Blocked trades by scope

- **7d:** blocked_total=2000
- **14d:** blocked_total=2000
- **30d:** blocked_total=2000
- **last100:** blocked_total=342
- **last387:** blocked_total=1764
- **last750:** blocked_total=2000

## A3 shadow deltas by scope

- **7d:** additional_admitted=151, estimated_pnl_delta_usd=-11.82 (proxy)
- **14d:** additional_admitted=151, estimated_pnl_delta_usd=-11.82 (proxy)
- **30d:** additional_admitted=151, estimated_pnl_delta_usd=-11.82 (proxy)
- **last100:** additional_admitted=151, estimated_pnl_delta_usd=-11.82 (proxy)
- **last387:** additional_admitted=151, estimated_pnl_delta_usd=-11.82 (proxy)
- **last750:** additional_admitted=151, estimated_pnl_delta_usd=-11.82 (proxy)

## Stability vs regime sensitivity

Time windows (7d, 14d, 30d) can be regime-sensitive; exit-count scopes (last100, last387, last750) smooth over time. Use last387 as governing baseline; 7d/14d as context for recent regime.

## Recommendation

- **Scope governing NEXT live decision:** last387
- **Context-only scopes:** 7d, 14d, 30d, last100, last750
- **Rationale:** last387 is the agreed learning baseline; other scopes provide regime sensitivity and stability context.

## Board persona verdicts (A3: Promote / Hold / Discard; advance to live paper test?)

### Adversarial

MULTI_SCOPE_COMPARATIVE_REVIEW shows A3 shadow deltas by scope; 7d/14d may be regime-sensitive. Recommend Hold A3 until 30d or last387 shadow is stable; do not advance to live paper test on 7d alone.

### Quant

Compare PnL and A3 estimated_pnl_delta across scopes; if last387 and 30d align, A3 is stable. Promote A3 to live paper test only if governing scope (last387) and 30d both show acceptable proxy delta.

### Product Operator

Use multi-scope view to prioritize which scope drives the next feature (e.g. exit vs gate). A3: Hold until Product agrees which scope is the success metric; then advance to live paper test.

### Risk

Stability vs regime: 7d/14d can swing; last387 and 30d are more stable. Discard A3 for live if any scope shows tail-risk note or large negative delta. Hold A3 until Risk signs off on governing scope.

### Execution Sre

Verify all scope artifacts exist on droplet and synthesis ran. Promote A3 only after SRE confirms no config/restart drift. Advance to live paper test only with rollback procedure documented.
