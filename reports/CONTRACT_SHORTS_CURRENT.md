# Shorts Contract — Current Behavior

**Document:** `reports/CONTRACT_SHORTS_CURRENT.md`  
**Purpose:** Establish where short orders are allowed/blocked and runtime shorts sanity check.

---

## 1. Config

- **`LONG_ONLY`** (env, default `"false"`): when `"true"`, all short (sell-side) entries are blocked.
- **Shorts “enabled”** = `LONG_ONLY` is `false`. Shorts are **supposed** to be enabled in live per project rules.

---

## 2. Where shorts are allowed/blocked

| Location | Behavior |
|----------|----------|
| **`main.py` Config** | `LONG_ONLY = get_env("LONG_ONLY", "false").lower() == "true"` |
| **`main.py` ~7516–7537** | **Long-only gate:** `if Config.LONG_ONLY and side == "sell"` → block, `log_event("gate", "long_only_blocked_short_entry", ...)`, `log_blocked_trade(..., "long_only_blocked_short_entry")`, continue. |
| **`main.py` ~3439–3450** | **`submit_entry` / Phase 2:** Alpaca `asset.shortable` check. If not shortable → `log_event("submit_entry", "asset_not_shortable_blocked", ...)`, return `None, ..., "asset_not_shortable"`. |
| **Signal → side** | Bearish direction → `side = "sell"`. Long-only gate runs **before** `submit_entry`. |

---

## 3. Decision path

1. Cluster direction **bearish** → `side = "sell"`.
2. If `Config.LONG_ONLY` → block with `long_only_blocked_short_entry`, never call `submit_entry`.
3. If not LONG_ONLY → we proceed to `submit_entry`. There, `asset.shortable` can still block.

So **short side is permitted** only when **both**:

- `LONG_ONLY` is `false`, and  
- we do not block earlier (e.g. score, capacity), and  
- `submit_entry` is reached and the asset is shortable.

---

## 4. Runtime sanity check (`shorts_mismatch`)

**Contract:** If config says shorts enabled (`LONG_ONLY` false) but we **never** permit short side, we emit:

```
logs/system_events.jsonl:
  subsystem="posture"
  event_type="shorts_mismatch"
  severity="CRITICAL"
  details={config_value, observed_behavior, code_path}
```

**Implementation:**

- **When we block with `long_only_blocked_short_entry`:** we only do so when `Config.LONG_ONLY` is True. If we ever blocked that way while `LONG_ONLY` is False, that is a bug → treat as `shorts_mismatch` (config says enabled, we blocked as “long-only”).
- **Startup / once per cycle:** If `LONG_ONLY` is False, we may emit `shorts_enabled_ack` (INFO) to confirm config. `verify_alpha_upgrade` checks that there is no `shorts_mismatch` CRITICAL when shorts are intended enabled, and that a short decision path (e.g. `side == "sell"` → `submit_entry`) exists.

---

## 5. Files

| Item | Location |
|------|----------|
| `LONG_ONLY` config | `main.py` Config |
| Long-only gate | `main.py` ~7516–7537 |
| Asset shortable check | `main.py` ~3439–3450 |
| System events | `utils.system_events.log_system_event`, `logs/system_events.jsonl` |
