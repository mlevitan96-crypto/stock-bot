/**
 * PR Risk Classifier — Automation instructions for Cursor Cloud Agent
 * Trigger: Pull request opened or updated.
 *
 * Copy or adapt this logic into the automation prompt at cursor.com/automations.
 */

// === INSTRUCTIONS FOR THE AGENT ===
//
// 1. Obtain the PR context: repo, branch, base, diff (files changed and patch).
//
// 2. Analyze the diff for the following dimensions (score each 0 = none, 1 = low, 2 = medium, 3 = high):
//
//    a) BLAST_RADIUS
//       - How many files/subsystems touched? (e.g. single script vs src/ + scripts/ + config)
//       - Are only docs/reports touched? → 0. Config only? → 1. Core paths (src/, scripts/governance)? → 2–3.
//
//    b) INFRA_IMPACT
//       - Changes to .github/, Docker, deploy scripts, cron, systemd, env or secrets usage → raise.
//       - No infra paths → 0.
//
//    c) TRADING_LOGIC_IMPACT
//       - Changes under src/ that affect signals, execution, risk, exit, sizing → 2–3.
//       - Only tests or telemetry logging → 1. No trading code → 0.
//
//    d) GOVERNANCE_IMPACT
//       - Changes to memory_bank/, reports/audit/, reports/board/, CSA/SRE scripts, deploy gates → 2–3.
//       - Docs or non-gate reports → 1. None → 0.
//
//    e) CONFIG_CHANGES
//       - .env, env files, feature flags, policy_variants, droplet authority → 1–3.
//       - No config → 0.
//
//    f) DEPENDENCY_CHANGES
//       - requirements.txt, package.json, new deps, version bumps → 1–2.
//       - None → 0.
//
// 3. Classify overall risk:
//    - LOW:   All dimensions 0–1 and no single dimension ≥ 2.
//    - MEDIUM: Any dimension 2, or multiple 1s across infra/trading/governance.
//    - HIGH:   Any dimension 3, or (infra + trading), or (governance + trading) both ≥ 2.
//
// 4. Post a single PR comment (use "Comment on pull request" tool) with this structure:
//
//    ## PR Risk Classification
//    **Risk level:** LOW | MEDIUM | HIGH
//
//    **Reasoning:**
//    - Blast radius: ...
//    - Infra impact: ...
//    - Trading logic impact: ...
//    - Governance impact: ...
//    - Config changes: ...
//    - Dependency changes: ...
//
//    **Recommended reviewers:** (e.g. "someone familiar with trading logic" if trading impact; "governance/CSA" if governance impact)
//
// 5. If risk is HIGH:
//    - Add label "requires-governance-review" to the PR (if the tool supports it; otherwise state in comment).
//    - If SLACK_WEBHOOK_URL is set in environment, send a short notification to the configured Slack channel: PR title, link, risk HIGH, and that governance review is required.
//
// 6. If risk is LOW and AUTO_APPROVE_LOW_RISK is true in environment:
//    - Approve the PR (only if "Approve pull request" tool is enabled for this automation).
//
// 7. Do not modify any code or repo files; only comment, label, and optionally notify Slack.

export const RISK_LEVELS = ['LOW', 'MEDIUM', 'HIGH'] as const;
export type RiskLevel = (typeof RISK_LEVELS)[number];

export interface RiskDimensions {
  blast_radius: number;
  infra_impact: number;
  trading_logic_impact: number;
  governance_impact: number;
  config_changes: number;
  dependency_changes: number;
}

export function classifyRisk(dims: RiskDimensions): RiskLevel {
  const { blast_radius, infra_impact, trading_logic_impact, governance_impact } = dims;
  if (Object.values(dims).some((v) => v >= 3)) return 'HIGH';
  if (infra_impact >= 2 && trading_logic_impact >= 2) return 'HIGH';
  if (governance_impact >= 2 && trading_logic_impact >= 2) return 'HIGH';
  if (Object.values(dims).some((v) => v >= 2)) return 'MEDIUM';
  return 'LOW';
}
