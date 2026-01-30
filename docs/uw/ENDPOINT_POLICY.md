# UW Endpoint Policy

**Points to:** `config/uw_endpoint_policies.py` and `scripts/audit_uw_endpoints.py`.

## Static Audit

Run before CI/regression:

```bash
python scripts/audit_uw_endpoints.py
```

- Extracts allowed endpoints from `unusual_whales_api/api_spec.yaml`.
- Scans codebase for UW endpoint usage.
- **Fails** if any referenced endpoint is not in the spec.

## Runtime Enforcement

- `src/uw/uw_client.py` validates each endpoint against the spec before making HTTP calls.
- Invalid endpoints log `uw_invalid_endpoint_attempt` and return without calling UW.
- See `run_regression_checks.py` for regression coverage of invalid-endpoint blocking.
