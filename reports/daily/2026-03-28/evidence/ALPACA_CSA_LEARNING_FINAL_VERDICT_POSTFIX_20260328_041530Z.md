# CSA learning final verdict (postfix)

**CSA_LEARNING_BLOCKED**

- **Reason:** Postfix window contains **zero** closed trades after `NEW_DEPLOY_FLOOR_TS` (`1774670865`); last-5 learning-only audit cannot pass.
- **trade_ids:** none in window
- **Missing live-truth fields:** not applicable — no postfix cohort to certify

Do **not** unblock learning until `alpaca_postfix_learning_n_audit.py` exits 0 with five completes.
