# Board verification: Banner & situation strip no longer stuck on “Loading”

**Date:** 2026-03-03  
**Fix:** Server-side render of direction banner and situation strip into initial HTML.

## Adversarial

- **Risk:** First paint could show wrong or stale data if sync helpers fail or read wrong paths.  
- **Mitigation:** Helpers use same data sources as `/api/direction_banner` and `/api/situation`; on exception we pass safe fallbacks (e.g. “Direction status unavailable”, “—” for situation). No trading logic or endpoints changed.

## SRE

- **Observability:** Banners no longer depend on client JS fetch; first load always shows data or explicit fallback.  
- **Deploy:** No new env vars or services; deploy is `git pull` + app restart.  
- **Rollback:** Revert template to static “Loading…” and remove server-rendered variables if needed.

## Product

- **Outcome:** Operators see trades reviewed, promotion idea, closed/open counts and direction status on first paint, so they can assess performance and improvement without waiting or seeing “Loading…” indefinitely.

## Verification

1. Open dashboard `/` (no auth required for banner/situation data).  
2. **Direction banner:** Shows message/detail/link or “Direction status unavailable” (never “Loading direction status…”).  
3. **Situation strip:** Shows “Trades reviewed: X/100”, “Promotion: …”, “Closed (90d): …”, “Open: …” or “—” (never “Loading situation…”).  
4. JS still refreshes both on an interval (e.g. 60s) without flashing “Loading…”.
