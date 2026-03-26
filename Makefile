# Stock-bot Makefile
# See memory_bank/TELEMETRY_STANDARD.md and scripts/audit/telemetry_integrity_gate.py

.PHONY: telemetry_gate help verify_report_layout prune_reports repo_report_cleanup ensure_daily_stubs

help:
	@echo "Targets:"
	@echo "  make telemetry_gate        - Run telemetry integrity gate (strict canonical)."
	@echo "  make telemetry_gate_legacy - Run gate allowing legacy records without canonical fields."
	@echo "  make verify_report_layout  - CI-style check for new report paths under reports/daily/."
	@echo "  make prune_reports         - Prune stale reports (retention_days=3)."
	@echo "  make repo_report_cleanup   - Move/delete legacy reports/ per lockdown rules (destructive)."
	@echo "  make ensure_daily_stubs    - Stub DAILY_* for sessions that have evidence only."

telemetry_gate:
	$(PYTHON) scripts/audit/telemetry_integrity_gate.py

telemetry_gate_legacy:
	$(PYTHON) scripts/audit/telemetry_integrity_gate.py --allow-legacy

verify_report_layout:
	$(PYTHON) scripts/maintenance/verify_report_layout.py --base origin/main || $(PYTHON) scripts/maintenance/verify_report_layout.py --base HEAD~1

prune_reports:
	$(PYTHON) scripts/maintenance/prune_stale_reports.py --retention-days 3

repo_report_cleanup:
	$(PYTHON) scripts/maintenance/repo_wide_report_cleanup.py --retention-days 3 --apply

ensure_daily_stubs:
	$(PYTHON) scripts/maintenance/ensure_daily_stubs_for_evidence_sessions.py

PYTHON ?= python3
