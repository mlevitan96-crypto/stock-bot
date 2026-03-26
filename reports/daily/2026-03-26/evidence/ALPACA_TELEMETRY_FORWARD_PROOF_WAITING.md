# Forward proof — waiting

- **Post-epoch exit count (approx):** 0
- **Required before proof:** ≥ 50
- Check: `python3` one-liner on droplet counting exits with `timestamp >= repair_iso_utc`.
- Re-run: `python3 scripts/alpaca_telemetry_forward_proof.py --min-trades 50`
