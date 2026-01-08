# Standard Operating Procedure: Generating Trading Reports

**Purpose:** Ensure all trading reports use correct data source and pass validation  
**Last Updated:** 2026-01-08  
**Status:** MANDATORY - Follow without exception

---

## CRITICAL RULE

**ALL TRADING REPORTS MUST FETCH DATA FROM DROPLET PRODUCTION SERVER**

**NEVER use local files** (`logs/`, `state/`, `data/`) for production reports.

---

## PROCEDURE

### Step 1: Import Required Modules

```python
from report_data_fetcher import ReportDataFetcher
from report_data_validator import validate_report_data, validate_data_source
from datetime import datetime, timezone
```

### Step 2: Initialize Data Fetcher

```python
# Specify date (YYYY-MM-DD) or use today
date = "2026-01-08"

# Create fetcher - this connects to Droplet
fetcher = ReportDataFetcher(date=date)

# Always use context manager to ensure connection is closed
with fetcher:
    # Fetch all required data
    trades = fetcher.get_executed_trades()
    blocked = fetcher.get_blocked_trades()
    signals = fetcher.get_signals()
    orders = fetcher.get_orders()
    gate_events = fetcher.get_gate_events()
    uw_attribution = fetcher.get_uw_attribution()
    
    # Get data source info for report metadata
    data_source_info = fetcher.get_data_source_info()
```

### Step 3: Validate Data Source

```python
# CRITICAL: Verify data came from Droplet, not local files
try:
    validate_data_source(data_source_info)
except ValidationError as e:
    print(f"VALIDATION FAILED: {e}")
    sys.exit(1)
```

### Step 4: Validate Data Quality

```python
# CRITICAL: Validate data before generating report
try:
    validation_report = validate_report_data(
        executed_trades=trades,
        blocked_trades=blocked,
        signals=signals,
        date=date,
        allow_zero_trades=False  # Set True only if market was closed
    )
    
    # Check for warnings
    if validation_report["warnings"]:
        for warning in validation_report["warnings"]:
            print(f"WARNING: {warning}")
    
except ValidationError as e:
    print(f"DATA VALIDATION FAILED: {e}")
    sys.exit(1)
```

### Step 5: Generate Report

```python
# Include data source info in report
report = {
    "report_date": date,
    "report_generated_at": datetime.now(timezone.utc).isoformat(),
    "data_source": data_source_info["source"],
    "data_fetch_timestamp": data_source_info["fetch_timestamp"],
    "executed_trades": {
        "count": len(trades),
        # ... analysis ...
    },
    # ... rest of report ...
}
```

### Step 6: Include Data Source in Report Output

**In Markdown reports:**
```markdown
**Report Generated:** 2026-01-08T21:30:00+00:00
**Data Source:** Droplet Production Server
**Data Fetched:** 2026-01-08T21:29:45+00:00
```

**In JSON reports:**
```json
{
  "report_date": "2026-01-08",
  "report_generated_at": "2026-01-08T21:30:00+00:00",
  "data_source": "Droplet Production Server",
  "data_fetch_timestamp": "2026-01-08T21:29:45+00:00"
}
```

### Step 7: Pre-Commit Validation

**Before committing, verify:**

1. ✅ Report lists "Droplet" or "Production Server" as data source
2. ✅ Trade count > 0 (or explicit reason documented)
3. ✅ Fetch timestamp is recent (< 1 hour old)
4. ✅ Data validation passed
5. ✅ No obvious errors in report (0 trades when bot is active = red flag)

**If any check fails:**
- DO NOT commit
- Fix the issue
- Re-run report generation
- Re-validate

---

## EXAMPLE: Complete Report Generation Script

```python
#!/usr/bin/env python3
"""
Example: Proper report generation following SOP
"""

import sys
from report_data_fetcher import ReportDataFetcher
from report_data_validator import validate_report_data, validate_data_source, ValidationError
from datetime import datetime, timezone

def generate_report(date: str):
    """Generate trading report following SOP"""
    
    # Step 1-2: Initialize and fetch data
    fetcher = ReportDataFetcher(date=date)
    
    try:
        with fetcher:
            # Fetch all data
            trades = fetcher.get_executed_trades()
            blocked = fetcher.get_blocked_trades()
            signals = fetcher.get_signals()
            orders = fetcher.get_orders()
            gate_events = fetcher.get_gate_events()
            
            # Get data source info
            data_source_info = fetcher.get_data_source_info()
            
            # Step 3: Validate data source
            try:
                validate_data_source(data_source_info)
                print(f"✓ Data source validated: {data_source_info['source']}")
            except ValidationError as e:
                print(f"✗ VALIDATION FAILED: {e}", file=sys.stderr)
                sys.exit(1)
            
            # Step 4: Validate data quality
            try:
                validation_report = validate_report_data(
                    executed_trades=trades,
                    blocked_trades=blocked,
                    signals=signals,
                    date=date,
                    allow_zero_trades=False
                )
                
                if validation_report["warnings"]:
                    for warning in validation_report["warnings"]:
                        print(f"⚠ WARNING: {warning}", file=sys.stderr)
                
                print(f"✓ Data validation passed")
                print(f"  Executed trades: {len(trades)}")
                print(f"  Blocked trades: {len(blocked)}")
                print(f"  Signals: {len(signals)}")
                
            except ValidationError as e:
                print(f"✗ DATA VALIDATION FAILED: {e}", file=sys.stderr)
                sys.exit(1)
            
            # Step 5-6: Generate report with data source info
            report = {
                "report_date": date,
                "report_generated_at": datetime.now(timezone.utc).isoformat(),
                "data_source": data_source_info["source"],
                "data_fetch_timestamp": data_source_info["fetch_timestamp"],
                "executed_trades": {
                    "count": len(trades),
                    # ... analysis ...
                },
                # ... rest of report ...
            }
            
            return report
            
    except Exception as e:
        print(f"✗ ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report = generate_report(date)
    print(f"Report generated successfully for {date}")
```

---

## COMMON MISTAKES TO AVOID

### ❌ WRONG: Reading from local files
```python
# DON'T DO THIS
from pathlib import Path
trades = []
with open("logs/attribution.jsonl") as f:
    for line in f:
        trades.append(json.loads(line))
```

### ✅ CORRECT: Using ReportDataFetcher
```python
# DO THIS INSTEAD
from report_data_fetcher import ReportDataFetcher
fetcher = ReportDataFetcher(date="2026-01-08")
with fetcher:
    trades = fetcher.get_executed_trades()
```

### ❌ WRONG: Skipping validation
```python
# DON'T DO THIS
trades = fetcher.get_executed_trades()
# Generate report without validation
```

### ✅ CORRECT: Always validate
```python
# DO THIS INSTEAD
trades = fetcher.get_executed_trades()
validate_report_data(trades, blocked, signals, date=date)
```

### ❌ WRONG: Not including data source
```markdown
## Report
Generated: 2026-01-08
Trades: 65
```

### ✅ CORRECT: Include data source
```markdown
## Report
Generated: 2026-01-08T21:30:00+00:00
**Data Source:** Droplet Production Server
**Data Fetched:** 2026-01-08T21:29:45+00:00
Trades: 65
```

---

## TROUBLESHOOTING

### Issue: "0 trades found"

**Possible Causes:**
1. Data not fetched from Droplet (used local files)
2. Date is incorrect (market was closed)
3. Bot was not running
4. No trading occurred (rare)

**Solution:**
1. Verify using `ReportDataFetcher` (not local files)
2. Check `data_source_info["source"]` is "Droplet Production Server"
3. Verify date is correct (market was open)
4. Check Droplet status: `ssh alpaca "systemctl status trading-bot.service"`

### Issue: "Connection failed"

**Possible Causes:**
1. SSH config issue
2. Droplet unavailable
3. Network issue

**Solution:**
1. Test SSH: `ssh alpaca "echo 'connected'"`
2. Check Droplet status
3. Verify `droplet_config.json` or SSH config

### Issue: "Validation failed: Invalid data source"

**Possible Causes:**
1. Data came from local files instead of Droplet

**Solution:**
1. Ensure using `ReportDataFetcher`, not direct file reads
2. Verify `data_source_info["source"]` contains "Droplet"

---

## REFERENCES

- **Root Cause Analysis:** `RCA_MISSING_TRADE_DATA_IN_REPORTS.md`
- **Memory Bank:** `MEMORY_BANK.md` - Section "CRITICAL: REPORT GENERATION DATA SOURCE RULE"
- **Data Fetcher Module:** `report_data_fetcher.py`
- **Data Validator Module:** `report_data_validator.py`
- **Working Example:** `fetch_droplet_data_and_generate_report.py`

---

**Status:** ✅ ACTIVE - Follow this procedure for all report generation  
**Enforcement:** Validation errors will block commits if pre-commit hooks are installed  
**Violations:** Report generation without following this SOP is a critical error
