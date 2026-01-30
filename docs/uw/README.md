# UW (Unusual Whales) Canonical Rules — Stock-Bot

**Canonical reference for all Unusual Whales API usage in stock-bot.**

## No Hallucinated Endpoints

- **All endpoints MUST exist** in `unusual_whales_api/api_spec.yaml`.
- **Static audit:** `scripts/audit_uw_endpoints.py` — fails CI/regression if code references unknown endpoints.
- **Runtime blocking:** `src/uw/uw_client.py` rejects invalid endpoints and logs `uw_invalid_endpoint_attempt` before any network call.

## Central Routing

- **All UW HTTP calls MUST route through** `src/uw/uw_client.py` (rate-limited, cached, logged).
- Scoring and decision code MUST **never** call UW directly.
- Scoring MUST read **only from cached intel artifacts** (uw_flow_cache, premarket_intel, postmarket_intel, uw_expanded_intel).

## Symbol-Level Scope

- Symbol-level UW calls are allowed **only for** `daily_universe ∪ core_universe`.
- Universe build MUST happen before market open.

## Single-Instance Ingestion

- **UW polling MUST be single-instance** (quota safety):
  - `uw_flow_daemon.py` MUST NOT run more than once on the droplet.
  - Systemd service `uw-flow-daemon.service` is the canonical runner.
  - File lock at `state/uw_flow_daemon.lock` prevents duplicates.
- See `scripts/install_uw_flow_daemon_systemd.py` for installation.

## Quota & TTL Rules

- **Usage state:** `state/uw_usage_state.json` — persisted daily usage.
- **Cache policy:** TTL enforced per endpoint policy in `config/uw_endpoint_policies.py`.
- **Backoff:** `uw_client` implements rate limiting and backoff on 429.
- See `docs/uw/ENDPOINT_POLICY.md` for policy references.

## Artifact-Only Consumption in Scoring

| Artifact | Location | Populated by |
|----------|----------|--------------|
| uw_flow_cache | data/uw_flow_cache.json | uw_flow_daemon |
| premarket_intel | state/premarket_intel.json | scripts/run_premarket_intel.py |
| postmarket_intel | state/postmarket_intel.json | scripts/run_postmarket_intel.py |
| uw_expanded_intel | data/uw_expanded_intel.json | run_intel_producers_on_droplet |

Scoring MUST read only from these artifacts. Never call UW from scoring paths.

## References

- `config/uw_endpoint_policies.py` — endpoint policies
- `scripts/audit_uw_endpoints.py` — static endpoint audit
- `MEMORY_BANK.md` §7.8 — UW Intelligence Layer invariants
