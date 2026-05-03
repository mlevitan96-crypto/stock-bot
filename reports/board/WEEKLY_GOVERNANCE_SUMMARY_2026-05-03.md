# Weekly Governance Summary — 2026-05-03

**Period:** 2026-04-26 to 2026-05-03

---

## Commits to main

**55 commits** landed on `origin/main` during this period. Key themes:

| Theme | Count | Highlights |
|-------|-------|------------|
| UI / Dashboard | 4 | Complete Tailwind institutional rewrite (`dba42416`), DASHBOARD_HTML serve fix, OPA dashboard integration, capped UI payloads + broker KPIs |
| Operations / Infra | 3 | Sovereign V3 root (`/root/stock-bot-v3`), dashboard port 5005, UFW hardening (allow 5005, deny 5000/5001), Monday flatten timer |
| Options / Wheel | 1 | Options engine, SP100 gate, put wall, IV/earnings, manager (`6f7bd609`) |
| UW Integration | 14 | WebSocket flow-alerts + REST budget tiers, REST quota circuit breaker @ 0.92, 50k/day REST cap, RTH quota throttle, Spot GEX spine, regime matrix (GEX/DP/sweeps), file-backed UWRegimeMatrix, WS Bearer auth, smoke tests |
| V2 ML / Gate | 8 | Densify fills missing manifest features with 0.0, v2_ml_row key resolution, train-serve skew fix (v2_uw_inputs → entry_uw), ML blobs on trade_intent snapshot, V2 veto diagnostics |
| Alpha 11 / Offense | 7 | Ensemble Alpha11 funnel + ablation harness, conviction sleeve sizing, offensive pivot (inversion engine, profit ladders), Alpha11 default flow floor 0.75, CHOP floor defaults, flow_strength mapping repairs |
| Signal / Telemetry | 6 | Shadow layer sync, signal tightening (bridge live UW to snapshot), conviction-to-flow UW merge, swarm-repair signal sparsity, exit explainability bug fix, feature density restoration |
| Paper / Live | 3 | V2 short quarantine lift + bidirectional live paper trading, MIN_NOTIONAL unlock, PDT API field deprecation |
| Debug / Chore | 5 | v2_killchain, sparse_row_dna_smoke, Dense DNA grep-equivalent, droplet .env sanitize, UW WS cron install |
| Docs / Memory | 4 | Memory bank updates (UFW, UW OpenAPI path, WS 401 scope note), 360 profitability reviewer persona, telemetry changelog sync |

<details>
<summary>Full commit list (55 commits)</summary>

```
dba42416 feat(ui): complete decoupling and institutional Tailwind rewrite
3a5bb364 docs(memory): §6.3.1 UFW hardening — allow 5005, deny 5000/5001
e9a5fcc9 feat(ops): sovereign V3 root /root/stock-bot-v3, dashboard port 5005, Monday flatten timer
e8136904 fix(dashboard): serve DASHBOARD_HTML from / instead of legacy static/index.html
194bed7f feat: alpha squeeze sitter scoring, capital velocity exits, Greek HUD
520e3be9 feat: OPA dashboard integration and risk-engine hardening
6f7bd609 feat(wheel): options engine, SP100 gate, put wall, IV/earnings, manager
55df729c fix: preserve existing epoch_state.json keys when anchoring
ff95b892 feat: latency interrupt, epoch reset, and strict telegram milestones
453b8952 feat: offensive pivot - inversion engine, profit ladders, removed streak shield
6ff79770 chore(droplet): install weekday 09:00 ET cron for UW regime matrix refresh
2e42e9d2 fix(uw): file-backed UWRegimeMatrix; shadow path skips live uw_get
0aed314b UW regime matrix: live GEX, dark pool, sweep extraction via uw_get
89475579 Add UW regime matrix shadow dictionary (GEX, DP, sweeps)
66fb3ede Add congressional regime watchlist and V2 gate conviction discount
85fe9a32 fix(alpaca): throttle Vanguard LOCKED Telegram to once per UTC day; V2 gate 0.30
07eabe9d chore(debug): v2_last_trade_intent_receipt for Dense DNA grep-equivalent
d5e237b8 chore(debug): v2_sparse_row_dna_smoke for droplet PYTHONPATH checks
bac5aece fix(v2): densify fills all missing manifest features with neutral 0.0
ee6880a7 fix(debug): syntax error in v2_killchain_last10 REPO path
e66f2af2 fix(v2): densify v2_ml_row for intel embed, symbol_enc, UW keys
f307cb30 fix(alpaca): ML blobs on trade_intent snapshot + learn_from_trade_close why_sentence kwarg
b9a0c2ee feat(alpaca): embed v2_ml_row on v2 veto trade_intent + dump audit script
9c1e8035 fix(alpaca): V2 gate row key resolution, string numerics, and veto diagnostics
d2adfdf6 fix(alpaca): synchronize shadow layer signals and upgrade board personas
58af2f73 fix(alpaca): final signal tightening - bridge live cluster UW to telemetry snapshot
9ea0385c test(alpaca): cover conviction-to-flow UW merge
9a03ae07 fix(alpaca): map UW conviction into flow_strength for snapshot density
952751e5 fix(alpaca): swarm-repair signal sparsity, fix exit explainability bug, and restore feature density
be8ba288 fix(alpaca): revert tracer threshold and mute God Tier upstream telegram spam
c3388443 fix(alpaca): resolve train-serve skew by mapping v2_uw_inputs to entry_uw for Vanguard ML gate
1abbb0bd fix(alpaca): log V2 and VPIN vetoes as blocked trade intents in run.jsonl
dab73955 fix(alpaca): repair severed flow_strength mapping in Alpha 11 gate
150b8ccd test(e2e): Ghost Whale integration seam audit (UW WS → gate → ML → Alpaca mock)
dfb18a7b fix(uw-ws): default WebSocket auth to query token; document vendor requirement
633384d2 docs(memory): UW OpenAPI primary path is repo root api_spec.yaml
8afb049f fix(uw): vendor OpenAPI at repo root; remove non-spec stock volume path
1e44134a feat(uw): REST quota circuit breaker at 0.92; droplet WS verify+deploy
1c39b9d5 feat(uw): 50k/day REST cap, RTH quota throttle, Spot GEX spine
4d61c3bd chore(debug): droplet .env sanitize (sed + dequote) and WS re-verify over SSH
6f027092 fix(debug): WS smoke test retry extra_headers on TypeError from handshake
9405fe34 chore(debug): add UW WebSocket smoke test (uw_ws_connect_config)
da2e512c fix(uw): WS recv loop + Bearer connect; expand radar candidates
a0bbf887 docs(memory): note UW WebSocket 401 when API key lacks WS scope
b5f34034 fix(uw): WS flow-alerts REST-shape shim for ML/composite parity
e84c8187 feat(uw): Sniper WebSocket flow-alerts + REST budget tiers
2eaf26af feat(offense): conviction sleeve sizing + ablation auto-tune hints
c3cefb65 feat(alpaca): ensemble Alpha11 funnel + entry funnel ablation harness
e194cb69 docs(alpaca): instantiate 360 profitability reviewer persona
57c135f9 paper: MIN_NOTIONAL unlock; Alpha11 CHOP floor add defaults to 0
511e5a42 docs(alpaca): sync memory bank and telemetry changelog for V2 short lift
3101570f feat(alpaca): lift V2 short quarantine and enable bidirectional live paper trading
7f27493a fix(alpaca): Alpha11 default flow floor 0.75, fix metadata lock imports
a07f045b chore(alpaca): drop deprecated PDT API fields ahead of broker removal
8fbdf528 perf(dashboard): cap UI payloads, broker KPIs from Alpaca, chained polling
```

</details>

---

## PRs merged

No merged PRs found in the last 7 days via GitHub CLI. Manual check recommended: [GitHub PR list, merged in last 7 days](../../.github).

> Commits appear to have been pushed directly to `main` (55 commits without corresponding merged PRs in the `gh` CLI results).

---

## CSA verdicts

No `CSA_VERDICT_*.json` or `CSA_VERDICT_LATEST.json` files found in `reports/audit/`.

---

## SRE anomalies

No `SRE_STATUS.json` or equivalent SRE status file found in `reports/audit/`.

Existing audit artifacts (not date-gated to this week, present in tree):
- `reports/audit/csa_paper_only_proof.txt`
- `reports/audit/stockbot_is_enabled.txt`
- `reports/audit/governance_loop_log_tail.txt`
- `reports/audit/stockbot_status_after.txt` / `stockbot_status_before.txt`
- `reports/audit/alpaca_env_placeholder.txt`
- `reports/audit/last_5_trades_droplet.txt` / `last_5_trades_after_prefix_fix.txt`
- `reports/audit/CURSOR_AUTOMATIONS_UI_RUNBOOK.md`
- `reports/audit/DASHBOARD_TAB_LIVE_DATA_AUDIT_20260327.md`

---

## Deploys

No `DEPLOYMENT_PROOF_*`, `DEPLOY_*`, or `B2_*` proof files were updated or created in `reports/audit/` during this period.

Deploy-related commits observed in git history:
- `1e44134a` feat(uw): REST quota circuit breaker at 0.92; **droplet WS verify+deploy**
- `e9a5fcc9` feat(ops): sovereign V3 root `/root/stock-bot-v3`, dashboard port 5005, Monday flatten timer

---

## Shadow / paper / live changes

| Mode | Change | Commit |
|------|--------|--------|
| **Paper** | MIN_NOTIONAL unlock; Alpha11 CHOP floor defaults to 0 | `57c135f9` |
| **Paper → Live** | Lift V2 short quarantine — enable bidirectional live paper trading | `3101570f` |
| **Shadow** | Shadow layer signal sync; shadow path skips live `uw_get` | `d2adfdf6`, `2e42e9d2` |
| **Shadow** | UW regime matrix shadow dictionary (GEX, DP, sweeps) | `89475579` |
| **Live** | Alpha11 default flow floor raised to 0.75; metadata lock imports fixed | `7f27493a` |
| **Live** | PDT API field deprecation (drop deprecated fields ahead of broker removal) | `a07f045b` |

A Gemini options-wheel strategy review was also generated: `reports/Gemini/OPTIONS_WHEEL_STRATEGY_REVIEW_2026-05-01.md`.

---

## Config changes

| File | Commit | Summary |
|------|--------|---------|
| `config/alpaca_risk_profile.json` | `453b8952` | Offensive pivot — inversion engine, profit ladders, removed streak shield |
| `config/paper_mode_config.py` | `57c135f9` | MIN_NOTIONAL unlock; Alpha11 CHOP floor defaults to 0 |
| `config/registry.py` | `520e3be9`, `ff95b892`, `1c39b9d5` | OPA dashboard + risk-engine hardening; latency interrupt + epoch reset; UW 50k/day REST cap + RTH quota |
| `config/strategies.yaml` | `194bed7f`, `520e3be9`, `6f7bd609` | Alpha squeeze sitter scoring + Greek HUD; OPA integration; options engine SP100 gate + put wall |

---

*Generated by Cursor Automation (weekly_governance_summary). Period: 2026-04-26 → 2026-05-03.*
