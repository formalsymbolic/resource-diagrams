"""
Structural analysis of string diagrams.

This module provides functions for walking StringDiagram objects and
identifying features related to copying (Fork/Δ) and deletion or linear use
(Stem/⊤). It is particularly useful when modeling systems in which some
elements (such as policies or tool definitions) are treated as copyable data
while others are not.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from .diagram import (
    DiagramElement,
    Fork,
    Sequential,
    Stem,
    StringDiagram,
    Tensor,
    Triangle,
    Wire,
)


Severity = Literal["high", "medium", "low"]


@dataclass
class SecurityFinding:
    """A single structured finding from diagram analysis."""
    severity: Severity
    category: str
    message: str
    recommendation: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityReport:
    """Structured security analysis report for an agent diagram."""
    title: str
    summary: str
    overall_risk: Literal["high", "medium", "low"]
    findings: List[SecurityFinding]
    raw_geometry: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "overall_risk": self.overall_risk,
            "findings": [
                {
                    "severity": f.severity,
                    "category": f.category,
                    "message": f.message,
                    "recommendation": f.recommendation,
                    "evidence": f.evidence,
                }
                for f in self.findings
            ],
            "raw_geometry": self.raw_geometry,
            "metadata": self.metadata,
        }


def analyze_safety_geometry(diagram: StringDiagram | DiagramElement) -> Dict[str, Any]:
    """
    Lightweight structural walk (maintained for compatibility).

    Returns raw counts and flags. Most new code should use
    generate_security_report for richer output.
    """
    if isinstance(diagram, StringDiagram):
        root = diagram.root
    else:
        root = diagram

    stats: Dict[str, Any] = {
        "policy_forks": 0,
        "one_way_paths": 0,
        "stems": 0,
        "has_structural_policy_copy": False,
        "has_explicit_guards": False,
        "notes": [],
    }

    def walk(elem: DiagramElement) -> None:
        if isinstance(elem, Triangle):
            if "policy" in str(elem).lower() or "tool" in str(elem).lower():
                stats["notes"].append(f"Found policy/tool triangle: {elem}")
        elif isinstance(elem, Fork):
            stats["policy_forks"] += 1
            stats["has_structural_policy_copy"] = True
            stats["notes"].append("Structural Δ fork detected on policy path")
        elif isinstance(elem, Stem):
            stats["stems"] += 1
            stats["one_way_paths"] += 1
            stats["has_explicit_guards"] = True
            stats["notes"].append("Explicit Stem (⊤ delete) — guarded one-way channel")
        elif isinstance(elem, Wire):
            stats["one_way_paths"] += 1
        elif isinstance(elem, Sequential):
            walk(elem.first)
            walk(elem.second)
        elif isinstance(elem, Tensor):
            walk(elem.left)
            walk(elem.right)

    walk(root)
    return stats


def generate_security_report(
    diagram: StringDiagram | DiagramElement,
    title: Optional[str] = None,
) -> SecurityReport:
    """
    Analyze a diagram and return a structured report describing its
    copy (Fork) and termination (Stem) structure.

    This is useful when the distinction between copyable and non-copyable
    elements is of interest.
    """
    raw = analyze_safety_geometry(diagram)

    findings: List[SecurityFinding] = []
    title = title or "Diagram Analysis"

    # High-severity: policy copying exists with no explicit guards on one-way paths
    if raw["policy_forks"] > 0 and not raw["has_explicit_guards"]:
        findings.append(
            SecurityFinding(
                severity="high",
                category="Policy Persistence",
                message=(
                    f"{raw['policy_forks']} structural policy/tool forks (Δ) detected "
                    "with no explicit Stem (⊤) termination on one-way channels."
                ),
                recommendation=(
                    "Consider inserting explicit Stems on sensitive observation or "
                    "user-data paths after first use, or scoping policy copies to "
                    "narrower objects. Review any path where copied policy can reach "
                    "tool invocations alongside user data."
                ),
                evidence={"policy_forks": raw["policy_forks"], "stems": raw["stems"]},
            )
        )

    # Medium: policy copying present (expected in many designs) but worth noting
    if raw["policy_forks"] > 0 and raw["has_explicit_guards"]:
        findings.append(
            SecurityFinding(
                severity="medium",
                category="Policy Copying",
                message=(
                    f"{raw['policy_forks']} policy/tool Δ forks present alongside "
                    f"{raw['stems']} explicit guards."
                ),
                recommendation=(
                    "Verify that guards (Stems) are placed on all sensitive one-way "
                    "channels. Policy copying is often legitimate; the risk is "
                    "unbounded lifetime for user data or secrets alongside it."
                ),
                evidence={"policy_forks": raw["policy_forks"], "stems": raw["stems"]},
            )
        )

    # Low / informational: purely one-way paths with no policy activity
    if raw["policy_forks"] == 0 and raw["one_way_paths"] > 0:
        findings.append(
            SecurityFinding(
                severity="low",
                category="Information Flow",
                message="Diagram contains only one-way paths with no policy copying.",
                evidence={"one_way_paths": raw["one_way_paths"]},
            )
        )

    # Determine overall risk
    if any(f.severity == "high" for f in findings):
        overall_risk: Literal["high", "medium", "low"] = "high"
        summary = (
            "High-risk geometry: policy copying without corresponding guards on "
            "one-way channels. This pattern is associated with persistence and "
            "exfiltration surfaces in agent scaffolds."
        )
    elif any(f.severity == "medium" for f in findings):
        overall_risk = "medium"
        summary = (
            "Moderate policy copying detected with some guards present. "
            "Review placement of termination (Stem) operations on sensitive paths."
        )
    else:
        overall_risk = "low"
        summary = "No high-risk policy-copying surfaces detected in this diagram."

    return SecurityReport(
        title=title,
        summary=summary,
        overall_risk=overall_risk,
        findings=findings,
        raw_geometry=raw,
        metadata={"analyzer_version": "0.2"},
    )
