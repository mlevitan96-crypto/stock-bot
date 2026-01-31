"""governance_chair — synthesizes agent verdicts, requires consensus."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parents[2]


def run_governance_chair(agent_verdicts: List[Dict[str, Any]], date: str) -> Dict[str, Any]:
    """
    Governance chair requires at least one SUPPORT and no OPPOSE for promotion.
    Returns synthesis verdict.
    """
    supports = sum(1 for v in agent_verdicts if v.get("verdict") == "SUPPORT")
    opposes = sum(1 for v in agent_verdicts if v.get("verdict") == "OPPOSE")
    abstains = sum(1 for v in agent_verdicts if v.get("verdict") == "ABSTAIN")
    if opposes > 0:
        return {
            "agent": "governance_chair",
            "verdict": "REJECT",
            "reason": f"{opposes} agent(s) oppose; promotion blocked",
            "details": [v for v in agent_verdicts if v.get("verdict") == "OPPOSE"],
        }
    if supports >= 1:
        return {
            "agent": "governance_chair",
            "verdict": "PROPOSE",
            "reason": f"{supports} support(s), {abstains} abstain(s); eligible for proposal",
            "details": agent_verdicts,
        }
    return {
        "agent": "governance_chair",
        "verdict": "REJECT",
        "reason": f"All abstain ({abstains}); insufficient consensus",
        "details": agent_verdicts,
    }
