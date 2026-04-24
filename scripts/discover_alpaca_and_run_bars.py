#!/usr/bin/env python3
"""
DISCOVER ALPACA CREDENTIALS + ENABLE REAL BARS (ONE BLOCK)
Run on droplet at /root/stock-bot. No guessing. No hardcoding. Hard fails.

Phases:
  0 — Locate live Alpaca credentials from systemd service
  1 — Export to .env.research, write alpaca_env_source.md
  2 — Verify Alpaca access with real API call
  3 — Run bars pipeline (real data only)
  4 — Final proof (parquet + PROOF.md)

Required output: one block printed at end.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) != "/root/stock-bot":
    print("RUN ON DROPLET: must run at /root/stock-bot", file=sys.stderr)
    sys.exit(1)

ENV_RESEARCH = REPO / ".env.research"
REPORTS_BARS = REPO / "reports" / "bars"
SOURCE_MD = REPORTS_BARS / "alpaca_env_source.md"
PARQUET = REPO / "data" / "bars" / "alpaca_daily.parquet"
PROOF_MD = REPORTS_BARS / "PROOF.md"

REQUIRED_KEYS = ("ALPACA_API_KEY", "ALPACA_SECRET_KEY", "ALPACA_BASE_URL")
# Default BASE_URL when service does not set it (paper trading)
DEFAULT_ALPACA_BASE_URL = "https://paper-api.alpaca.markets"


def run_cmd(cmd: list[str], timeout: int = 30, env: dict | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd,
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env or os.environ,
        )
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return -1, str(e)


def phase0_discover_credentials() -> tuple[str, dict[str, str]]:
    """Find Alpaca keys from live trading systemd service. Return (service_name, {key: val})."""
    # List candidate services
    code, out = run_cmd(
        ["systemctl", "list-units", "--type=service", "--no-pager", "--plain", "--no-legend"],
        timeout=10,
    )
    if code != 0:
        print("ALPACA KEYS NOT FOUND IN SERVICE ENV")
        sys.exit(1)
    candidates = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        unit = line.split()[0]
        name = unit.lower()
        if any(x in name for x in ("stock", "trade", "bot", "main", "alpaca", "supervisor")):
            candidates.append(unit)
    if not candidates:
        print("ALPACA KEYS NOT FOUND IN SERVICE ENV")
        sys.exit(1)

    # Prefer stock-bot if present
    service = None
    for c in candidates:
        if c == "stock-bot.service" or c.startswith("stock-bot"):
            service = c
            break
    if not service:
        service = candidates[0]

    # Get environment: Environment=, EnvironmentFiles=, EnvironmentFile=, FragmentPath=, WorkingDirectory=
    code, out = run_cmd(
        [
            "systemctl", "show", service,
            "--property=Environment",
            "--property=EnvironmentFiles",
            "--property=EnvironmentFile",
            "--property=FragmentPath",
            "--property=WorkingDirectory",
        ],
        timeout=10,
    )
    if code != 0:
        print("ALPACA KEYS NOT FOUND IN SERVICE ENV")
        sys.exit(1)

    env_vars: dict[str, str] = {}
    env_files: list[str] = []

    for line in out.splitlines():
        line = line.strip()
        if line.startswith("Environment="):
            rest = line[len("Environment=") :].strip()
            if not rest:
                continue
            for part in re.split(r"\s+(?=[A-Z_]+=)", rest):
                if "=" not in part:
                    continue
                k, _, v = part.partition("=")
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k in REQUIRED_KEYS:
                    env_vars[k] = v
        if line.startswith("EnvironmentFiles=") or line.startswith("EnvironmentFile="):
            key = "EnvironmentFiles=" if line.startswith("EnvironmentFiles=") else "EnvironmentFile="
            rest = line[len(key) :].strip()
            for path in rest.split():
                path = path.lstrip("-").strip()
                if path and path not in env_files:
                    env_files.append(path)
        if line.startswith("WorkingDirectory="):
            wd = line[len("WorkingDirectory=") :].strip()
            if wd:
                env_file_in_wd = Path(wd) / ".env"
                if env_file_in_wd.exists() and str(env_file_in_wd) not in env_files:
                    env_files.append(str(env_file_in_wd))
        if line.startswith("FragmentPath="):
            frag = line[len("FragmentPath=") :].strip()
            if frag and Path(frag).exists():
                try:
                    for uline in Path(frag).read_text(encoding="utf-8", errors="replace").splitlines():
                        uline = uline.strip()
                        if uline.startswith("EnvironmentFile="):
                            p = uline[len("EnvironmentFile=") :].strip().lstrip("-").strip()
                            if p and p not in env_files:
                                env_files.append(p)
                        if uline.startswith("Environment="):
                            rest = uline[len("Environment=") :].strip()
                            for part in re.split(r"\s+(?=[A-Z_]+=)", rest):
                                if "=" not in part:
                                    continue
                                k, _, v = part.partition("=")
                                k, v = k.strip(), v.strip().strip('"').strip("'")
                                if k in REQUIRED_KEYS:
                                    env_vars[k] = v
                except Exception:
                    pass

    # Read env files (same source as live)
    for fpath in env_files:
        if len(env_vars) >= 2:  # at least API_KEY + SECRET_KEY
            break
        p = Path(fpath)
        if not p.exists():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k in REQUIRED_KEYS and k not in env_vars:
                    env_vars[k] = v
        except Exception:
            continue

    missing = [k for k in ("ALPACA_API_KEY", "ALPACA_SECRET_KEY") if not (env_vars.get(k) or "").strip()]
    if missing:
        print("ALPACA KEYS NOT FOUND IN SERVICE ENV")
        sys.exit(1)
    if not (env_vars.get("ALPACA_BASE_URL") or "").strip():
        env_vars["ALPACA_BASE_URL"] = DEFAULT_ALPACA_BASE_URL
    return service, env_vars


def phase1_export_research(service_name: str, env_vars: dict[str, str]) -> None:
    """Write .env.research and reports/bars/alpaca_env_source.md."""
    REPORTS_BARS.mkdir(parents=True, exist_ok=True)
    lines = [f"{k}={env_vars[k]}" for k in REQUIRED_KEYS]
    ENV_RESEARCH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ENV_RESEARCH.chmod(0o600)
    source_lines = [
        "# Alpaca env source (research)",
        "",
        "Credentials sourced from **live trading systemd service** (no duplication, no hardcoding).",
        "",
        f"- **Service:** `{service_name}`",
        "- **File:** `.env.research` (chmod 600)",
        "- **Keys:** ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL",
        "",
    ]
    SOURCE_MD.write_text("\n".join(source_lines), encoding="utf-8")


def phase2_verify_alpaca(env: dict[str, str]) -> bool:
    """Real Alpaca Data API call. Return True iff status 200."""
    base = env.get("ALPACA_BASE_URL", "")
    data_url = base.replace("paper-api", "data.alpaca.markets").rstrip("/")
    if not data_url.startswith("http"):
        data_url = "https://data.alpaca.markets"
    url = f"{data_url}/v2/stocks/bars"
    try:
        import urllib.request
        import urllib.parse
        req = urllib.request.Request(
            url + "?" + urllib.parse.urlencode({"symbols": "SPY", "timeframe": "1Day", "limit": 5}),
            headers={
                "APCA-API-KEY-ID": env["ALPACA_API_KEY"],
                "APCA-API-SECRET-KEY": env["ALPACA_SECRET_KEY"],
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            status = r.getcode()
            body = r.read().decode("utf-8", errors="replace")[:300]
    except Exception as e:
        print("STATUS: (request failed)")
        print("BODY:", str(e)[:300])
        print("ALPACA DATA ACCESS FAILED")
        sys.exit(1)
    print("STATUS:", status)
    print("BODY:", body)
    if status != 200:
        print("ALPACA DATA ACCESS FAILED")
        sys.exit(1)
    return True


def phase3_run_bars_pipeline(env: dict[str, str]) -> tuple[bool, int, str, str, float, float, float, bool]:
    """Run run_bars_pipeline.py with research env. Return (env_pass, symbols_fetched, date_range, cov_min, cov_med, cov_max, pnl_nonzero)."""
    env_pass = True
    symbols_fetched = 0
    date_range = ""
    cov_min = cov_med = cov_max = 0.0
    pnl_nonzero = False
    full_env = os.environ.copy()
    full_env.update(env)
    code, out = run_cmd(
        [sys.executable, "scripts/run_bars_pipeline.py"],
        timeout=900,
        env=full_env,
    )
    print(out)
    if code != 0:
        verdict = "BARS MISSING — FIX REQUIRED"
    else:
        verdict = "BARS READY — REAL PNL ENABLED"
    # Parse one-block style from pipeline output
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("Symbols fetched:"):
            try:
                symbols_fetched = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("Date range covered:"):
            date_range = line.split(":", 1)[1].strip()
        elif "Bars coverage:" in line or "min/median/max" in line:
            m = re.search(r"(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)", line)
            if m:
                cov_min, cov_med, cov_max = float(m.group(1)), float(m.group(2)), float(m.group(3))
        elif line.startswith("Replay pnl non-zero:"):
            pnl_nonzero = "YES" in line
    return env_pass, symbols_fetched, date_range, cov_min, cov_med, cov_max, pnl_nonzero


def phase4_final_proof() -> bool:
    """Confirm parquet and PROOF.md exist and non-empty."""
    if not PARQUET.exists() or PARQUET.stat().st_size == 0:
        return False
    if not PROOF_MD.exists() or not PROOF_MD.read_text(encoding="utf-8", errors="replace").strip():
        return False
    return True


def main() -> int:
    # Phase 0
    service_name, env_vars = phase0_discover_credentials()
    # Phase 1
    phase1_export_research(service_name, env_vars)
    # Phase 2
    phase2_verify_alpaca(env_vars)
    # Phase 3
    env_pass, symbols_fetched, date_range, cov_min, cov_med, cov_max, pnl_nonzero = phase3_run_bars_pipeline(env_vars)
    # Phase 4
    proof_ok = phase4_final_proof()
    if not proof_ok:
        pnl_nonzero = False

    # Required one-block output
    print()
    print("============================================================")
    print("REQUIRED OUTPUT (DISCOVER + BARS)")
    print("============================================================")
    print("Alpaca credential source:", service_name)
    print("Alpaca API verification: PASS")
    print("Symbols fetched:", symbols_fetched)
    print("Date range covered:", date_range or "(none)")
    print("Bars coverage: min/median/max % —", f"{cov_min}/{cov_med}/{cov_max}")
    print("Replay pnl non-zero:", "YES" if pnl_nonzero else "NO")
    if proof_ok and pnl_nonzero:
        print("Verdict: BARS READY — REAL PNL ENABLED")
    else:
        print("Verdict: BARS MISSING — FIX REQUIRED")
    print("============================================================")
    return 0 if (proof_ok and pnl_nonzero) else 1


if __name__ == "__main__":
    sys.exit(main())
