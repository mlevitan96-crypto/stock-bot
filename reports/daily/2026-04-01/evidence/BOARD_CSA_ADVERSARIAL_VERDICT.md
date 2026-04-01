# CSA adversarial memo — integrity closure

## Did we preserve fail-closed contracts?

**Mostly yes.** Arming still requires full `_checkpoint_100_integrity_ok` (DATA_READY, thresholds, strict ARMED *for session-scoped evaluation*, exit tail schema). No bypass of strict or gates was introduced. **Caveat:** era-scoped strict export can remain BLOCKED while session strict is ARMED — operators must not conflate the two when claiming “strict is green” globally.

## Remaining ambiguity in “armed”

Two notions: **strict LEARNING_STATUS ARMED** (session floor) vs **milestone `integrity_armed`** (epoch after `arm_epoch_utc`). Documentation and board packets should label which floor was used.

## Telegram governance loopholes

- **systemd paths:** post-close and failure-detector are now integrity-gated via unit env.
- **Manual / cron / SSH one-offs:** can still send if run without `TELEGRAM_GOVERNANCE_INTEGRITY_ONLY=1`. Recommend optional global `.env` flag if policy is absolute single-authority.

## Recommendation

Add a one-line banner to weekly board packets: **strict scope = session vs era** when citing `LEARNING_STATUS`.
