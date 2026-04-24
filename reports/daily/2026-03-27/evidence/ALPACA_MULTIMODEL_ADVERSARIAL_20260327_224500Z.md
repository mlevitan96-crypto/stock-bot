# ALPACA — Multi-model adversarial review (Phase 5)

Three independent **logical** reviewers (SRE-Automation, Quant-Strict, Red-Team). Disagreements reconciled against droplet artifacts in this folder.

## Reviewer A — SRE-Automation

| Claim | Verdict |
|--------|---------|
| Telegram silence explained | **Agree** — journal shows exit **4** / Memory Bank gate, not Telegram HTTP failure. |
| Scheduler blame | **Agree** — timer fired; failure is app precondition. |
| After MB append | **Agree** — dry-run exit 0 proves send path reachable. |

**Highest-risk blind spot:** Droplet `MEMORY_BANK.md` is **not** cleanly tracked; markers can regress on `git reset` or manual edits without CI guard.

**Falsifier:** `journalctl` shows successful post-close with `telegram_ok` true in audit JSONL for `2026-03-27` after timer — would contradict “only MB blocked.”

## Reviewer B — Quant-Strict

| Claim | Verdict |
|--------|---------|
| “Decision-grade PnL” for today | **Partial** — session open→16:00 strict gate **ARMED**, but dashboard-era cohort **BLOCKED** with 2 incomplete trades. |
| Fee completeness | **Disagree with “complete”** — **0** fee extractions from `orders.jsonl`. |
| 255 vs 256 exits | **Note tension** — strict bounded window vs calendar-day exit rows; must be disclosed in any board number. |

**Highest-risk blind spot:** Symbol-level PnL sums ignore partial fills, corporate actions, and broker cash movements; net **1.91 USD** is not reconciled to Alpaca account day P&L in this artifact set.

**Falsifier:** Broker account snapshot for `2026-03-27` materially differs from **1.91** realized attribution sum.

## Reviewer C — Red-Team

| Claim | Verdict |
|--------|---------|
| “Secrets broken” hypothesis | **Reject** — `getMe` succeeded with detected env. |
| “Dedupe ate message” | **Reject** — no live attempt logged for session. |
| Synthetic watermark `2035-01-02` | **Flag** — stale watermark risks confusing operators; not today’s root cause but harms trust in state files. |

**Highest-risk blind spot:** MSFT incomplete example appears **twice** in audit JSON — could indicate duplicate exit rows or audit duplication; needs single-trade confirmation.

**Falsifier:** Prove Telegram sent to operator chat via chat logs while audit lacks `2026-03-27` success line.

## Disagreement table

| Topic | A | B | C | Reconciled conclusion |
|-------|---|---|---|------------------------|
| Root cause of silence | MB gate | MB gate | MB gate | **Unanimous: MB precondition.** |
| Is global strict “clean”? | Not asked | BLOCKED | — | **BLOCKED** (2 incomplete) is real for STRICT_EPOCH cohort. |
| Fees covered? | Not asked | No | — | **Not proven** from orders.jsonl. |
| MSFT duplicate rows | — | noise | suspicious | **Treat as one trade_key with duplicate incomplete examples** until proven otherwise. |

## Reconciled conclusion

Telegram diagnosis is **correct**: **runner ran, aborted on Memory Bank, no send.** PnL session slice is **internally consistent** for attribution JSONL but **not** fully decision-grade at the **dashboard strict** layer until the **2** incomplete trades and **fee** gaps are resolved or explicitly scoped out.
