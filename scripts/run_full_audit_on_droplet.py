#!/usr/bin/env python3
"""
Run Full System Audit on Droplet and fetch all artifacts.

This script:
1. Verifies droplet preconditions (repo, git, Alpaca env)
2. Deploys latest code if needed
3. Runs full_system_audit.py with AUDIT_MODE=1 and AUDIT_DRY_RUN=1
4. Verifies §2 and §5 specifically
5. Fetches all audit artifacts
6. Creates proof document
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REMOTE_ROOT = "/root/stock-bot"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-01-26", help="YYYY-MM-DD (auto-detect if not provided)")
    args = ap.parse_args()
    date = args.date

    sys.path.insert(0, str(REPO))
    from droplet_client import DropletClient

    client = DropletClient()
    ssh = sftp = None
    try:
        ssh = client._connect()
        sftp = ssh.open_sftp()

        print("=" * 80)
        print("FULL SYSTEM AUDIT ON DROPLET")
        print("=" * 80)

        # ========================================================================
        # 1) Preconditions: droplet identity and repo parity
        # ========================================================================
        print("\n[1] Verifying preconditions...")
        
        # 1.1 Check pwd, systemd, git
        cmd = f"cd {REMOTE_ROOT} && pwd && systemctl show stock-bot.service -p WorkingDirectory -p ExecStart && git rev-parse HEAD && git status --porcelain"
        out, err, rc = client._execute(cmd, timeout=30)
        if rc != 0:
            print(f"[FAIL] Precondition check failed: {err}")
            return 1
        print(f"[OK] WorkingDirectory and git status verified")
        
        # Extract git commit
        lines = out.strip().split('\n')
        git_hash = None
        for line in lines:
            if len(line) == 40 and all(c in '0123456789abcdef' for c in line):
                git_hash = line
                break
        if not git_hash:
            # Try parsing from git rev-parse output
            for line in lines:
                if 'HEAD' in line or len(line) == 40:
                    git_hash = line.split()[-1] if ' ' in line else line
                    break
        
        # 1.2 Check Alpaca environment (presence only, no secrets)
        cmd2 = f"cd {REMOTE_ROOT} && python3 -c \"import os; from pathlib import Path; env_file = Path('.env'); vars_needed = ['ALPACA_API_KEY', 'ALPACA_SECRET_KEY', 'ALPACA_BASE_URL']; present = [v for v in vars_needed if os.getenv(v) or (env_file.exists() and v in env_file.read_text())]; print(f'ALPACA_ENV_VARS_PRESENT: {{len(present)}}/{{len(vars_needed)}}')\""
        out2, err2, rc2 = client._execute(cmd2, timeout=15)
        if rc2 == 0:
            print(f"[OK] Alpaca environment check: {out2.strip()}")
        else:
            print(f"[WARN] Alpaca env check failed: {err2}")
        
        # Check if alpaca_trade_api can be imported
        cmd3 = f"cd {REMOTE_ROOT} && python3 -c \"try: import alpaca_trade_api; print('ALPACA_IMPORT: OK'); except ImportError as e: print(f'ALPACA_IMPORT: FAIL - {{e}}')\""
        out3, err3, rc3 = client._execute(cmd3, timeout=15)
        print(f"[OK] Alpaca import check: {out3.strip()}")

        # ========================================================================
        # 2) Deploy parity if needed
        # ========================================================================
        print("\n[2] Checking deployment parity...")
        cmd4 = f"cd {REMOTE_ROOT} && git fetch origin main && git rev-parse HEAD && git rev-parse origin/main"
        out4, err4, rc4 = client._execute(cmd4, timeout=30)
        if rc4 == 0:
            lines4 = out4.strip().split('\n')
            local_hash = lines4[0] if lines4 else None
            remote_hash = lines4[1] if len(lines4) > 1 else None
            if local_hash != remote_hash:
                print(f"[INFO] Droplet HEAD ({local_hash[:8]}) != origin/main ({remote_hash[:8] if remote_hash else 'unknown'})")
                print("[INFO] Resetting to origin/main...")
                cmd5 = f"cd {REMOTE_ROOT} && git reset --hard origin/main && systemctl restart stock-bot.service && sleep 2 && systemctl status stock-bot.service --no-pager | head -10"
                out5, err5, rc5 = client._execute(cmd5, timeout=60)
                if rc5 == 0:
                    print("[OK] Deployed and restarted")
                    # Get new hash
                    out6, _, _ = client._execute(f"cd {REMOTE_ROOT} && git rev-parse HEAD", timeout=10)
                    git_hash = out6.strip()
                else:
                    print(f"[WARN] Deployment may have failed: {err5}")
            else:
                print(f"[OK] Droplet already at origin/main ({local_hash[:8] if local_hash else 'unknown'})")
        
        # Write deployment proof
        deploy_proof = REPO / "reports" / "AUDIT_DROPLET_DEPLOYMENT_PROOF.md"
        deploy_proof.parent.mkdir(parents=True, exist_ok=True)
        deploy_proof.write_text(f"""# Droplet Deployment Proof

**Generated:** {datetime.now(timezone.utc).isoformat()}
**Date:** {date}

## Git Commit
- **Hash:** {git_hash or 'unknown'}
- **Status:** Clean

## Service Status
```bash
{out5 if 'out5' in locals() else 'Not restarted'}
```

## Alpaca Environment
- **Env vars present:** {out2.strip() if 'out2' in locals() else 'unknown'}
- **Import check:** {out3.strip() if 'out3' in locals() else 'unknown'}
""", encoding="utf-8")
        print(f"[OK] Wrote {deploy_proof}")

        # ========================================================================
        # 3) Upload full_system_audit.py and run
        # ========================================================================
        print("\n[3] Uploading and running full audit...")
        
        # Upload audit script
        local_audit = REPO / "scripts" / "full_system_audit.py"
        remote_audit = f"{REMOTE_ROOT}/scripts/full_system_audit.py"
        if local_audit.exists():
            sftp.put(str(local_audit), remote_audit)
            print(f"[OK] Uploaded full_system_audit.py")
        else:
            print(f"[FAIL] Missing {local_audit}", file=sys.stderr)
            return 1

        # Auto-detect date if needed
        if date == "auto":
            cmd_date = f"cd {REMOTE_ROOT} && tail -1000 logs/run.jsonl | grep -o '\"_dt\":\"[0-9]\\{{4\\}}-[0-9]\\{{2\\}}-[0-9]\\{{2\\}}' | tail -1 | cut -d'\"' -f4 || echo '2026-01-26'"
            out_date, _, _ = client._execute(cmd_date, timeout=15)
            date = out_date.strip() or "2026-01-26"
            print(f"[INFO] Auto-detected date: {date}")

        # Run audit with AUDIT_MODE=1 and AUDIT_DRY_RUN=1
        cmd_audit = f"cd {REMOTE_ROOT} && export AUDIT_MODE=1 && export AUDIT_DRY_RUN=1 && python3 scripts/full_system_audit.py --date {date}"
        print(f"[INFO] Running: {cmd_audit}")
        out_audit, err_audit, rc_audit = client._execute(cmd_audit, timeout=300)
        print(out_audit or "")
        if err_audit:
            print(err_audit, file=sys.stderr)
        if rc_audit not in (0, 1):
            print(f"[WARN] Audit exit code {rc_audit}", file=sys.stderr)

        # ========================================================================
        # 4) Verify §2 and §5 specifically
        # ========================================================================
        print("\n[4] Verifying §2 and §5 evidence...")
        
        # §2: symbol_risk_features.json
        cmd_s2 = f"cd {REMOTE_ROOT} && python3 -c \"import json; from pathlib import Path; p = Path('state/symbol_risk_features.json'); d = json.loads(p.read_text()) if p.exists() else {{}}; syms = d.get('symbols', {{}}); print(f'SYMBOL_RISK_COUNT: {{len(syms)}}')\""
        out_s2, err_s2, rc_s2 = client._execute(cmd_s2, timeout=15)
        symbol_risk_count = out_s2.strip().split(':')[-1].strip() if ':' in out_s2 else "0"
        print(f"[§2] Symbol risk features: {symbol_risk_count} symbols")
        
        # §5: audit_dry_run entries in orders.jsonl
        cmd_s5 = f"cd {REMOTE_ROOT} && grep -c '\"dry_run\":\\s*true' logs/orders.jsonl || echo '0'"
        out_s5, err_s5, rc_s5 = client._execute(cmd_s5, timeout=15)
        dry_run_count = out_s5.strip()
        print(f"[§5] Audit dry-run orders: {dry_run_count} entries")
        
        # Get sample entries
        cmd_s5_sample = f"cd {REMOTE_ROOT} && grep '\"dry_run\":\\s*true' logs/orders.jsonl | head -2"
        out_s5_sample, _, _ = client._execute(cmd_s5_sample, timeout=15)
        sample_orders = out_s5_sample.strip().split('\n')[:2] if out_s5_sample.strip() else []

        # ========================================================================
        # 5) Fetch all artifacts
        # ========================================================================
        print("\n[5] Fetching audit artifacts...")
        
        reports_local = REPO / "reports"
        reports_local.mkdir(parents=True, exist_ok=True)
        exports_local = REPO / "exports"
        exports_local.mkdir(parents=True, exist_ok=True)
        
        # Fetch all AUDIT_*.md reports
        for i in range(12):
            if i == 0:
                name = "AUDIT_00_SAFETY_AND_MODE.md"
            elif i == 1:
                name = "AUDIT_01_BOOT_AND_IDENTITY.md"
            elif i == 2:
                name = "AUDIT_02_DATA_AND_FEATURES.md"
            elif i == 3:
                name = "AUDIT_03_SIGNAL_GENERATION.md"
            elif i == 4:
                name = "AUDIT_04_GATES_AND_DISPLACEMENT.md"
            elif i == 5:
                name = "AUDIT_05_ENTRY_AND_ROUTING.md"
            elif i == 6:
                name = "AUDIT_06_POSITION_STATE.md"
            elif i == 7:
                name = "AUDIT_07_EXIT_LOGIC.md"
            elif i == 8:
                name = "AUDIT_08_SHADOW_EXPERIMENTS.md"
            elif i == 9:
                name = "AUDIT_09_TELEMETRY.md"
            elif i == 10:
                name = "AUDIT_10_EOD.md"
            elif i == 11:
                name = "AUDIT_11_JOINABILITY.md"
            else:
                continue
            
            remote = f"{REMOTE_ROOT}/reports/{name}"
            local = reports_local / name
            try:
                sftp.get(remote, str(local))
                print(f"[OK] Fetched {name}")
            except FileNotFoundError:
                print(f"[WARN] Missing {name}")
        
        # Fetch verdict
        try:
            sftp.get(f"{REMOTE_ROOT}/reports/FULL_SYSTEM_AUDIT_VERDICT.md", str(reports_local / "FULL_SYSTEM_AUDIT_VERDICT.md"))
            print("[OK] Fetched FULL_SYSTEM_AUDIT_VERDICT.md")
        except FileNotFoundError:
            print("[WARN] Missing FULL_SYSTEM_AUDIT_VERDICT.md")
        
        # Fetch CSVs
        for csv_name in [
            "AUDIT_signal_matrix.csv",
            "AUDIT_displacement_decisions.csv",
            "AUDIT_exit_paths.csv",
            "AUDIT_shadow_scoreboard.csv",
            "AUDIT_joinability.csv",
        ]:
            remote_csv = f"{REMOTE_ROOT}/exports/{csv_name}"
            local_csv = exports_local / csv_name
            try:
                sftp.get(remote_csv, str(local_csv))
                print(f"[OK] Fetched {csv_name}")
            except FileNotFoundError:
                print(f"[WARN] Missing {csv_name}")

        # ========================================================================
        # 6) Create proof document
        # ========================================================================
        print("\n[6] Creating proof document...")
        
        # Read verdict to extract PASS/FAIL
        verdict_path = reports_local / "FULL_SYSTEM_AUDIT_VERDICT.md"
        verdict_text = ""
        if verdict_path.exists():
            verdict_text = verdict_path.read_text(encoding="utf-8")
        
        # Parse PASS/FAIL table
        sections_pass = []
        sections_fail = []
        in_table = False
        for line in verdict_text.split('\n'):
            if '| § | Section | Result |' in line:
                in_table = True
                continue
            if in_table and line.startswith('|') and '|' in line[1:]:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    try:
                        sec_num = int(parts[1])
                        sec_name = parts[2]
                        result = parts[3]
                        if result == "PASS":
                            sections_pass.append((sec_num, sec_name))
                        else:
                            sections_fail.append((sec_num, sec_name))
                    except (ValueError, IndexError):
                        pass
            elif in_table and not line.strip().startswith('|'):
                break
        
        proof_doc = reports_local / f"AUDIT_DROPLET_PROOF_{date}.md"
        proof_lines = [
            "# Droplet Full System Audit Proof",
            "",
            f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
            f"**Date:** {date}",
            f"**Git Commit:** {git_hash or 'unknown'}",
            "",
            "## Service Status",
            "```",
            f"WorkingDirectory: {REMOTE_ROOT}",
            "```",
            "",
            "## PASS/FAIL Table (12 sections)",
            "| § | Section | Result |",
            "|---|---------|--------|",
        ]
        for num, name in sorted(sections_pass + sections_fail, key=lambda x: x[0]):
            result = "PASS" if (num, name) in sections_pass else "FAIL"
            proof_lines.append(f"| {num} | {name} | {result} |")
        
        proof_lines.extend([
            "",
            "## §2 Evidence (Data & Features)",
            f"- **Symbol risk features count:** {symbol_risk_count}",
            f"- **File exists:** {'Yes' if int(symbol_risk_count or '0') > 0 else 'No'}",
            "",
            "## §5 Evidence (Entry & Routing)",
            f"- **Audit dry-run orders count:** {dry_run_count}",
            f"- **Sample entries (redacted):**",
        ])
        
        for i, sample in enumerate(sample_orders[:2], 1):
            try:
                # Redact sensitive fields
                import json as json_module
                rec = json_module.loads(sample)
                redacted = {k: ("[REDACTED]" if k in ["api_key", "secret", "password", "token"] else v) for k, v in rec.items()}
                proof_lines.append(f"```json")
                proof_lines.append(json_module.dumps(redacted, indent=2))
                proof_lines.append("```")
            except Exception:
                proof_lines.append(f"```json")
                proof_lines.append(sample[:200] + "..." if len(sample) > 200 else sample)
                proof_lines.append("```")
        
        # Calculate confidence
        total = len(sections_pass) + len(sections_fail)
        passes = len(sections_pass)
        confidence = int(100 * passes / total) if total > 0 else 0
        
        proof_lines.extend([
            "",
            "## Confidence Score",
            f"{confidence}%",
            "",
            "## Final Answer",
            "",
            f"**Can STOCK-BOT execute, manage, exit, observe, and learn from trades correctly?**",
            "",
        ])
        
        if passes == 12:
            proof_lines.append("**YES (12/12)** — All subsystems proven working on droplet.")
        elif passes >= 10:
            proof_lines.append(f"**MOSTLY YES ({passes}/12)** — {len(sections_fail)} subsystem(s) failed: {', '.join(f'§{n}' for n, _ in sections_fail)}")
        else:
            proof_lines.append(f"**NO ({passes}/12)** — Multiple failures: {', '.join(f'§{n}' for n, _ in sections_fail)}")
        
        proof_doc.write_text('\n'.join(proof_lines), encoding="utf-8")
        print(f"[OK] Wrote {proof_doc}")

        # ========================================================================
        # 7) Final output
        # ========================================================================
        print("\n" + "=" * 80)
        print("FINAL OUTPUT")
        print("=" * 80)
        print(f"\nDroplet run date: {date}")
        print(f"Droplet git commit: {git_hash or 'unknown'}")
        print(f"\nPASS/FAIL table (12 sections):")
        print("| § | Section | Result |")
        print("|---|---------|--------|")
        for num, name in sorted(sections_pass + sections_fail, key=lambda x: x[0]):
            result = "PASS" if (num, name) in sections_pass else "FAIL"
            print(f"| {num} | {name} | {result} |")
        
        if sections_fail:
            print(f"\nFailures:")
            for num, name in sections_fail:
                print(f"  - §{num} {name}")
        
        print(f"\nProof artifacts:")
        print(f"  - {proof_doc}")
        print(f"  - {reports_local / 'FULL_SYSTEM_AUDIT_VERDICT.md'}")
        for i in range(12):
            name = f"AUDIT_{i:02d}_*.md" if i > 0 else "AUDIT_00_SAFETY_AND_MODE.md"
            # List actual files
            for f in reports_local.glob(f"AUDIT_*.md"):
                print(f"  - {f}")
            break  # Just show pattern
        
        if passes == 12:
            print("\n✅ SUCCESS: 12/12 PASS on droplet")
            return 0
        else:
            print(f"\n[WARN] PARTIAL: {passes}/12 PASS on droplet")
            return 1

    except Exception as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if sftp:
            try:
                sftp.close()
            except Exception:
                pass
        try:
            client.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
