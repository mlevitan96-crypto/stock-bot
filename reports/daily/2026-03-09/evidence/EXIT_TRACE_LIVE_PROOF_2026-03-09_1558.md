# Exit Trace LIVE PROOF — 2026-03-09_1558

**Generated:** 2026-03-09T15:58:18.389014+00:00

## Phase 0 — Droplet authority

- hostname: ubuntu-s-1vcpu-2gb-nyc3-01-alpaca
- git commit: 1da3913e3dc8
- system time (UTC): 2026-03-09T15:58:18Z
- python: Python 3.12.3
- stock-bot status: active

## Phase 1 — Trace emission context

- Open paper positions: 11

Waiting 130s for 2 sampling intervals...
## Phase 2 — Trace file

- File exists: yes
- Size: 76790 bytes
- Last 10 lines read: 10

- Samples with ts within 2 min: 10/10

## Phase 3 — Granularity & completeness (CSA)

- Sample 0 (open_GM_2026-03-09T14:17:07.451Z): OK
- Sample 1 (open_LOW_2026-03-09T14:17:32.392Z): OK
- Sample 2 (open_HD_2026-03-09T14:17:50.342Z): OK
- Sample 3 (open_GOOGL_2026-03-09T14:18:07.226Z): OK
- Sample 4 (open_XLP_2026-03-09T14:18:15.399Z): OK
- Sample 5 (open_XLV_2026-03-09T14:18:23.920Z): OK
- Sample 6 (open_XLF_2026-03-09T14:18:31.400Z): OK
- Sample 7 (open_DIA_2026-03-09T14:18:39.105Z): OK
- Sample 8 (open_BA_2026-03-09T14:19:12.392Z): OK
- Sample 9 (open_AAPL_2026-03-09T14:19:47.246Z): OK

## Phase 4 — Exit eligibility timeline

- Trade IDs in window: ['open_GM_2026-03-09T14:17:07.451Z', 'open_LOW_2026-03-09T14:17:32.392Z', 'open_HD_2026-03-09T14:17:50.342Z', 'open_GOOGL_2026-03-09T14:18:07.226Z', 'open_XLP_2026-03-09T14:18:15.399Z', 'open_XLV_2026-03-09T14:18:23.920Z', 'open_XLF_2026-03-09T14:18:31.400Z', 'open_DIA_2026-03-09T14:18:39.105Z', 'open_BA_2026-03-09T14:19:12.392Z', 'open_AAPL_2026-03-09T14:19:47.246Z']
- open_GM_2026-03-09T14:17:07.451Z: 1 sample(s)
- open_LOW_2026-03-09T14:17:32.392Z: 1 sample(s)
- open_HD_2026-03-09T14:17:50.342Z: 1 sample(s)
- open_GOOGL_2026-03-09T14:18:07.226Z: 1 sample(s)
- open_XLP_2026-03-09T14:18:15.399Z: 1 sample(s)
- open_XLV_2026-03-09T14:18:23.920Z: 1 sample(s)
- open_XLF_2026-03-09T14:18:31.400Z: 1 sample(s)
- open_DIA_2026-03-09T14:18:39.105Z: 1 sample(s)
- open_BA_2026-03-09T14:19:12.392Z: 1 sample(s)
- open_AAPL_2026-03-09T14:19:47.246Z: 1 sample(s)

- Values vary across samples: no (single sample or static)

## Phase 5–6 — CSA verdict & owner synthesis

- **Verdict:** EXIT_TRACE_PROVEN
- **Exit learning allowed:** True

### Owner synthesis

- **Is exit decision tracing LIVE on the droplet?** Yes
- **Is UW fully granular and populated?** Yes
- **Can we reconstruct peak unrealized and signal state?** Yes (trace has ts, unrealized_pnl, signals per sample)
- **Proceed to exit optimization?** Yes
