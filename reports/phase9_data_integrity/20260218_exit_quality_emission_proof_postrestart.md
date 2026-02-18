# Exit quality emission proof — post-restart (2026-02-18)

## A) Marker before waiting (run once)

```bash
cd /root/stock-bot
python3 - <<'PY'
import os
p="logs/exit_attribution.jsonl"
print("bytes", os.path.getsize(p))
PY
```

Paste: `bytes ________`

## B) After new exits (or after wait): sample newest 800 lines

```bash
tail -n 800 logs/exit_attribution.jsonl | python3 - <<'PY'
import sys, json
n=0; m=0; ex=[]
for line in sys.stdin:
  try: r=json.loads(line)
  except: continue
  n+=1
  if r.get("exit_quality_metrics") is not None:
    m+=1
    if len(ex)<2: ex.append(r.get("exit_quality_metrics"))
print("sample_records", n, "with_exit_quality_metrics", m)
print("examples", ex)
PY
```

## Result (paste here)

- **sample_records:** ___
- **with_exit_quality_metrics:** ___
- **examples:** ___

If with_exit_quality_metrics == 0: diagnose (new exits? right file? log_exit_attribution called? info["high_water"] at runtime?), add minimal logging if needed, re-test. STOP until non-zero.
