/**
 * PR Bug Review — Automation instructions for Cursor Cloud Agent
 * Trigger: Pull request opened or updated.
 *
 * Copy or adapt this logic into the automation prompt at cursor.com/automations.
 */

// === INSTRUCTIONS FOR THE AGENT ===
//
// 1. Obtain the full PR diff (files changed and patches) and repository context.
//
// 2. Perform a deep diff analysis. For each changed file and relevant hunk, check for:
//
//    a) LOGIC ERRORS
//       - Off-by-one, wrong condition (e.g. >= vs >), inverted boolean, wrong variable used.
//       - Incorrect aggregation or loop bounds.
//
//    b) REGRESSIONS
//       - Removal or weakening of validation, error handling, or guards.
//       - Behavior change that could break existing callers or contracts.
//
//    c) MISSING EDGE CASES
//       - Empty list, null/None, zero, negative numbers, empty string not handled.
//       - Timezone or boundary conditions (e.g. market open/close).
//
//    d) INCONSISTENT NAMING
//       - Same concept named differently (e.g. score vs composite_score); typos in public APIs.
//
//    e) DEAD CODE
//       - Unreachable branches, unused imports, commented-out logic that should be removed or restored.
//
//    f) MISSING TESTS
//       - New or modified behavior in src/ or critical scripts without corresponding test changes.
//       - Suggest where tests might be added (file or area).
//
// 3. For each finding:
//    - Prefer posting an **inline comment** on the specific line(s) when the tool supports it.
//    - Include: short title, what’s wrong, and a suggested fix or test location where possible.
//    - If inline comments are not available, post a single top-level comment with sections per file and line references.
//
// 4. Format per finding:
//    **[Category]** (Logic error | Regression | Edge case | Naming | Dead code | Missing tests)
//    - Location: file:line (or hunk)
//    - Issue: ...
//    - Suggestion: ...
//
// 5. Do not modify any code or repo files. Only post comments.
// 6. Be concise; avoid nitpicking style unless it affects correctness or maintainability.

export const CATEGORIES = [
  'logic_error',
  'regression',
  'edge_case',
  'naming',
  'dead_code',
  'missing_tests',
] as const;

export type FindingCategory = (typeof CATEGORIES)[number];

export interface Finding {
  category: FindingCategory;
  file: string;
  line?: number;
  message: string;
  suggestion?: string;
}
