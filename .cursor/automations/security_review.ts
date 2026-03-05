/**
 * Security Review — Automation instructions for Cursor Cloud Agent
 * Trigger: Push to main.
 *
 * Copy or adapt this logic into the automation prompt at cursor.com/automations.
 */

// === INSTRUCTIONS FOR THE AGENT ===
//
// 1. After a push to main, scan the repository (full tree or changed files in the push) for:
//
//    a) SECRETS AND CREDENTIAL LEAKS
//       - Hardcoded API keys, passwords, tokens, private keys (PEM, env vars in code).
//       - Patterns: ALPACA_, SECRET_, PASSWORD, api_key=, token=, Bearer [a-zA-Z0-9_-], .pem, PRIVATE KEY.
//       - Exclude: .env.example, docs that describe env var names without values, comments that say "set in env".
//
//    b) UNSAFE PATTERNS
//       - eval(), exec() with user or external input; unpickling untrusted data; SQL built from string concat.
//       - Unsafe deserialization, shell=True with user input, path traversal.
//
//    c) DEPENDENCY VULNERABILITIES
//       - If requirements.txt or package.json present: note that a dependency scan (e.g. pip-audit, npm audit) should be run in CI; flag any known critical deps from changelog or common CVE lists if you have context.
//
//    d) INSECURE NETWORK CALLS
//       - HTTP (not HTTPS) for sensitive endpoints; disabled cert verification (verify=False, NODE_TLS_REJECT_UNAUTHORIZED=0); missing timeouts or retries that could lead to hanging.
//
// 2. Severity:
//    - CRITICAL: Confirmed secret/credential in repo; RCE or critical unsafe pattern.
//    - HIGH: Likely secret pattern; unsafe deserialization or SQL injection risk; disabled TLS verification in production paths.
//    - MEDIUM: Suspicious pattern; dependency worth auditing; weak crypto or weak auth flow.
//    - LOW: Best-practice suggestions only.
//
// 3. Produce a summary (markdown) suitable for:
//    - GitHub Security tab or a dedicated security report artifact.
//    - If this run was triggered by a PR, also post as PR comment.
//
//    Structure:
//    ## Security Review (push to main)
//    **Commit / ref:** ...
//    **Findings:**
//    | Severity | Location | Description |
//    |----------|----------|-------------|
//    ...
//    **Recommendations:** ...
//
// 4. If any finding is HIGH or CRITICAL:
//    - Open a GitHub issue with title "[Security] ..." and the summary + recommendations.
//    - If SLACK_WEBHOOK_URL is set in environment, send a short notification to Slack: severity, repo, ref, and link to the issue (or summary).
//
// 5. Do not modify code or commit; only report. If you have "Open pull request" enabled and want to suggest a fix (e.g. remove a false-positive secret), do so in a separate run or manual step.

export const SEVERITY = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] as const;
export type Severity = (typeof SEVERITY)[number];

export interface SecurityFinding {
  severity: Severity;
  category: 'secret' | 'unsafe_pattern' | 'dependency' | 'network';
  location: string;
  description: string;
  recommendation?: string;
}
