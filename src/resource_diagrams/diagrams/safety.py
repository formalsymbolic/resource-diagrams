"""
Structural analysis of string diagrams (upgraded).

This module provides SafetyAnalyzer (and its convenience wrappers
analyze_safety_geometry / generate_security_report) for geometry review of
StringDiagram instances.

It performs path-sensitive influence tracking over Fork (Δ copy), Stem (⊤ delete),
Triangle (policy/program), Box (tool/reasoner steps), and the monoidal combinators.
The goal is to make visible whether sensitive one-way values actually reach
tool contexts in the presence of policy forks, and whether explicit Stems
terminate those paths afterward.

This remains an illustrative structural analysis aid and visualization helper,
not a formal security analyzer or verifier. The structured output (especially
the sensitive_reaches evidence and fork classifications) is intended to be
directly useful to human reviewers.

Added (illustrative structural metric for review):
    policy_copy_vs_sensitive_reach_summary : dict classifying policy vs. other
    forks and counting sensitive reaches that cross policy forks (coarse proxy
    for those without downstream stem termination at end of walk). Pure
    derivation from the path-sensitive data; stays within early-prototype
    honest positioning.

Short usage (illustrative, for review):
    from resource_diagrams.diagrams.safety import analyze_safety_geometry
    # d = ... (StringDiagram with policy forks + sensitive wires + optional stems)
    geom = analyze_safety_geometry(d)
    summary = geom.get("policy_copy_vs_sensitive_reach_summary")
    print(summary)  # e.g. {'policy_forks': 1, 'sensitive_reaches_under_policy_copy': 1, ...}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .diagram import (
    Box,
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
    """A single structured finding from diagram analysis.

    Strengthened invariant (construction-time): `severity` is a Literal
    constrained to {"high", "medium", "low"}; __post_init__ rejects any
    other value so invalid-severity findings are unrepresentable.
    """

    severity: Severity
    category: str
    message: str
    recommendation: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.severity not in ("high", "medium", "low"):
            raise ValueError(
                f"SecurityFinding.severity must be 'high'|'medium'|'low', got {self.severity!r}"
            )


@dataclass
class SecurityReport:
    """Structured diagram review report (illustrative) for an agent diagram.

    Strengthened invariant (construction-time): `overall_risk` is constrained
    to Literal high/medium/low at construction via __post_init__ (invalid
    risk levels unrepresentable).
    """

    title: str
    summary: str
    overall_risk: Literal["high", "medium", "low"]
    findings: list[SecurityFinding]
    raw_geometry: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.overall_risk not in ("high", "medium", "low"):
            raise ValueError(
                f"SecurityReport.overall_risk must be 'high'|'medium'|'low', got {self.overall_risk!r}"
            )

    def to_dict(self) -> dict[str, Any]:
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


class SafetyAnalyzer:
    """Path-sensitive geometry analyzer for string diagrams (policy vs. one-way flows) — illustrative review aid.

    This is the upgraded implementation.

    Capabilities beyond the original simple node counting + canned text:
    - Classifies every Fork and Stem by the *kind* of Object (policy, sensitive/user,
      context/memory, observation, resource, data). Exposed as forks_by_type etc.
    - Runs a live-influence dataflow: starts with empty live set; Wires/Triangles introduce
      influences; Forks add "*_copy_active" tags (duplicating policy reachability scenarios);
      Stems *remove* matching influences from the live set for everything downstream;
      Sequential passes live sets along the spine; Tensor unions parallel branches.
    - At every Box that looks like a tool or reasoner (by label or program_code), records
      a "reach" event for every sensitive influence that is still live at that point,
      together with whether any policy_copy_active influence is also live.
      This directly answers "does this sensitive one-way value reach a tool context
      under (a) policy fork scenario?"
    - After the full walk, computes whether any sensitive influence "persists" in the
      final live set (i.e. was never stemmed after its use sites).
    - All original simple counts/flags are still produced exactly for compatibility.

    The public functions delegate to an instance of this class.
    """

    def __init__(self, diagram: StringDiagram | DiagramElement) -> None:
        if isinstance(diagram, StringDiagram):
            self.root: DiagramElement = diagram.root
            self.title: str = diagram.title
        else:
            self.root = diagram
            self.title = getattr(diagram, "title", "element") if hasattr(diagram, "title") else "element"
        self._raw: dict[str, Any] | None = None

    def analyze(self) -> dict[str, Any]:
        if self._raw is not None:
            return self._raw
        self._raw = self._compute_geometry()
        return self._raw

    def _compute_geometry(self) -> dict[str, Any]:
        # All original keys are populated for 100% backward compat of callers
        # that only looked at policy_forks / stems / has_*/notes / one_way_paths.
        stats: dict[str, Any] = {
            "policy_forks": 0,
            "one_way_paths": 0,
            "stems": 0,
            "has_structural_policy_copy": False,
            "has_explicit_guards": False,
            "notes": [],
            # Richer fields (additive)
            "forks_by_type": {},
            "stems_by_type": {},
            "triangles_encountered": [],
            "boxes_encountered": [],
            "sensitive_reaches": [],
            "unguarded_sensitive_reaches": 0,
            "sensitive_persists": False,
            "classified_forks": 0,
            "flow_summary": {},
        }

        reaches: list[dict[str, Any]] = []
        simple_notes: list[str] = []

        def classify(obj: Any) -> str:
            s = str(obj).lower() if obj is not None else ""
            if any(k in s for k in ("policy", "agentpolicy", "tooldefs", "tool_def")):
                return "policy"
            if any(k in s for k in ("user", "query", "secret", "credential", "private", "fact", "sensitive")):
                return "sensitive"
            if any(k in s for k in ("memory", "context", "state")):
                return "context"
            if any(k in s for k in ("obs", "observation", "result", "observe")):
                return "observation"
            if any(k in s for k in ("token", "resource", "budget")):
                return "resource"
            return "data"

        def short_label(elem: DiagramElement) -> str:
            if isinstance(elem, Wire):
                return f"Wire({elem.label})"
            if isinstance(elem, Box):
                return f"Box({elem.label})"
            if isinstance(elem, Triangle):
                return f"Triangle(▼ {elem.program})"
            if isinstance(elem, Fork):
                return f"Fork(Δ {elem.obj})"
            if isinstance(elem, Stem):
                return f"Stem(⊤ {elem.obj})"
            if isinstance(elem, Sequential):
                return ";"
            if isinstance(elem, Tensor):
                return "⊗"
            return type(elem).__name__

        def is_tool_or_reasoner_context(b: Box) -> bool:
            lbl = (b.label or "").lower()
            pc = (b.program_code or "").lower()
            kws = ("tool", "search", "call", "execute", "web", "calc", "reason", "agent", "decide")
            return any(k in lbl or k in pc for k in kws)

        def flow(
            elem: DiagramElement, live: frozenset[str], path: tuple[str, ...]
        ) -> frozenset[str]:
            curr_path = path + (short_label(elem),)

            if isinstance(elem, Wire):
                cls = classify(elem.obj)
                infl = {f"{cls}:{elem.label or str(elem.obj)}"}
                if cls in ("sensitive", "data", "observation"):
                    stats["one_way_paths"] += 1
                return frozenset(set(live) | infl)

            if isinstance(elem, Triangle):
                prog = elem.program
                stats["triangles_encountered"].append(prog)
                is_pol = any(k in prog.lower() for k in ("policy", "tool", "agentpolicy"))
                cls = "policy" if is_pol else "program"
                infl = {f"triangle:{cls}:{prog[:40]}"}
                if is_pol:
                    stats["has_structural_policy_copy"] = True
                    simple_notes.append(f"Found policy/tool triangle: {elem}")
                return frozenset(set(live) | infl)

            if isinstance(elem, Fork):
                cls = classify(elem.obj)
                stats["forks_by_type"][cls] = stats["forks_by_type"].get(cls, 0) + 1
                stats["classified_forks"] += 1
                stats["policy_forks"] += 1  # compat: count every Fork as before
                if cls == "policy":
                    stats["has_structural_policy_copy"] = True
                    stats["policy_copy_scenarios"] = stats.get("policy_copy_scenarios", 0) + 1
                    simple_notes.append("Structural Δ fork detected on policy path")
                else:
                    simple_notes.append(f"Structural Δ fork on {cls} path ({elem.obj})")
                infl = {f"forked:{cls}:{elem.obj}", f"{cls}_copy_active"}
                return frozenset(set(live) | infl)

            if isinstance(elem, Stem):
                cls = classify(elem.obj)
                stats["stems_by_type"][cls] = stats["stems_by_type"].get(cls, 0) + 1
                stats["stems"] += 1
                stats["one_way_paths"] += 1
                stats["has_explicit_guards"] = True
                simple_notes.append("Explicit Stem (⊤ delete) — guarded one-way channel")
                obj_l = str(elem.obj).lower()
                new_live = {i for i in live if obj_l not in i.lower() and cls not in i.lower()}
                return frozenset(new_live)

            if isinstance(elem, Box):
                stats["boxes_encountered"].append(elem.label or elem.program_code or "unnamed_box")
                curr_live = set(live)
                if is_tool_or_reasoner_context(elem):
                    sens = [
                        i
                        for i in curr_live
                        if "sensitive" in i
                        or any(k in i.lower() for k in ("user", "query", "secret", "credential", "privatefact", "userprivate"))
                    ]
                    has_pol = any("policy" in i or "copy_active" in i or "triangle:policy" in i for i in curr_live)
                    for s in sens:
                        reach_ev = {
                            "sensitive": s,
                            "context": f"Box({elem.label or elem.program_code or 'unnamed'})",
                            "under_policy_copy": has_pol,
                            "path": list(curr_path[-5:]),
                        }
                        reaches.append(reach_ev)
                return frozenset(curr_live)

            if isinstance(elem, Sequential):
                after_first = flow(elem.first, live, curr_path)
                return flow(elem.second, after_first, curr_path)

            if isinstance(elem, Tensor):
                left_after = flow(elem.left, live, curr_path)
                right_after = flow(elem.right, live, curr_path)
                return left_after | right_after

            return live

        # Run the analysis
        final_live = flow(self.root, frozenset(), tuple())

        # Post-process
        stats["notes"] = simple_notes[:25]
        seen: set[tuple[str, str]] = set()
        unique_reaches: list[dict[str, Any]] = []
        for r in reaches:
            key = (r["sensitive"], r["context"])
            if key not in seen:
                seen.add(key)
                unique_reaches.append(r)
        stats["sensitive_reaches"] = unique_reaches
        stats["unguarded_sensitive_reaches"] = len(unique_reaches)
        stats["sensitive_persists"] = any(
            any(k in i.lower() for k in ("sensitive", "user", "query", "secret", "credential", "private"))
            for i in final_live
        )
        stats["flow_summary"] = {
            "final_live_influences": [x for x in final_live if not x.startswith("triangle:")][:10],
            "num_distinct_sensitive_reaches": len(unique_reaches),
            "has_policy_sensitive_co_flow": any(r.get("under_policy_copy") for r in unique_reaches),
            "sensitive_terminated": stats["stems"] > 0 and not stats["sensitive_persists"],
        }

        # Derived structural metric for reviewers (pure post-processing on existing data).
        # Preserves all prior keys for backward compatibility.
        forks_by = stats.get("forks_by_type", {})
        policy_fork_ct = forks_by.get("policy", 0)
        sens_reaches = stats.get("sensitive_reaches", [])
        under_pol_ct = sum(1 for r in sens_reaches if r.get("under_policy_copy", False))
        persisting = stats.get("sensitive_persists", False)
        stems_ct = stats.get("stems", 0)
        # Coarse proxy (end-of-diagram): sensitive under policy + overall persist (no full stem termination observed for live sensitives)
        unguarded_pol_crossings = under_pol_ct if (persisting and under_pol_ct > 0) else 0
        stats["policy_copy_vs_sensitive_reach_summary"] = {
            "policy_forks": policy_fork_ct,
            "total_forks_by_type": forks_by,
            "sensitive_reaches": len(sens_reaches),
            "sensitive_reaches_under_policy_copy": under_pol_ct,
            "sensitive_reaches_crossing_policy_fork_without_downstream_stem_proxy": unguarded_pol_crossings,
            "has_stems": stems_ct > 0,
            "sensitive_persists_at_end": persisting,
            "note": "Illustrative structural metric. The 'without downstream stem' uses a coarse whole-diagram persistence proxy from the path walk, not fine-grained per-reach tracking. Not a risk score, probability, or security claim.",
        }

        if stats["policy_forks"] > 0:
            stats["notes"].append(f"Total structural Δ forks (all types): {stats['policy_forks']}")
        if stats.get("stems"):
            stats["notes"].append(f"Total ⊤ stems: {stats['stems']}")

        if stats["stems"] > 0:
            stats["has_explicit_guards"] = True
        return stats

    def generate_report(self, title: str | None = None) -> SecurityReport:
        """Build the full review-oriented SecurityReport from the analyzed geometry."""
        raw = self.analyze()
        findings: list[SecurityFinding] = []
        title = title or f"Diagram Analysis: {self.title}"

        policy_forks = raw["policy_forks"]
        stems = raw["stems"]
        has_guards = raw["has_explicit_guards"]
        reaches = raw.get("sensitive_reaches", [])
        persists = raw.get("sensitive_persists", False)
        forks_by = raw.get("forks_by_type", {})
        stems_by = raw.get("stems_by_type", {})

        # Primary upgraded finding: concrete sensitive reach under policy fork, possibly unterminated
        if policy_forks > 0 and reaches and (not has_guards or persists):
            sample = reaches[0] if reaches else {}
            msg = (
                f"{policy_forks} policy/tool Δ fork(s) (types: {forks_by}) detected. "
                f"{len(reaches)} sensitive value(s) reach tool/reasoner context(s) while policy copies are live "
                f"(example: {sample.get('sensitive', '?')} → {sample.get('context', '?')}, "
                f"under_policy_copy={sample.get('under_policy_copy')}). "
                f"Sensitive persists after use sites: {persists}. Insufficient Stems."
            )
            findings.append(
                SecurityFinding(
                    severity="high",
                    category="Unguarded Sensitive Reachability",
                    message=msg,
                    recommendation=(
                        "Insert explicit Stem(⊤) on the sensitive object *after its use* in the tool context "
                        "(see guarded contrast pattern in models/agents.py). This bounds lifetime of user data "
                        "even while policy/tool definitions are legitimately copied via Δ. "
                        "The sensitive_reaches list in raw_geometry gives the exact paths for structural review."
                    ),
                    evidence={
                        "policy_forks": policy_forks,
                        "forks_by_type": forks_by,
                        "stems": stems,
                        "stems_by_type": stems_by,
                        "sensitive_reaches": reaches[:3],
                        "sensitive_persists": persists,
                        "flow_summary": raw.get("flow_summary"),
                    },
                )
            )

        # Medium when we have both forks and guards and saw reaches that got (partially) terminated
        elif policy_forks > 0 and has_guards:
            sample = reaches[0] if reaches else {}
            term_note = " (and terminated by subsequent Stem)" if not persists else ""
            msg = (
                f"{policy_forks} policy/tool Δ fork(s) (by type {forks_by}) alongside {stems} explicit Stem(s) "
                f"(by type {stems_by}). "
                f"Sensitive values reached context(s) under policy influence{term_note}."
            )
            findings.append(
                SecurityFinding(
                    severity="medium",
                    category="Policy Copying with Guards",
                    message=msg,
                    recommendation=(
                        "Confirm that every Stem appears *after* the consumption point on its sensitive path. "
                        "The raw_geometry.sensitive_reaches + flow_summary give the structured trace of "
                        "what actually flowed where. This is the minimal safe pattern for agents that must "
                        "copy policy while handling transient secrets/PII/observations."
                    ),
                    evidence={
                        "policy_forks": policy_forks,
                        "forks_by_type": forks_by,
                        "stems": stems,
                        "stems_by_type": stems_by,
                        "sensitive_reaches": reaches[:3],
                        "flow_summary": raw.get("flow_summary"),
                    },
                )
            )

        # Fallbacks for legacy/simple diagrams (preserve exact old messages/behavior)
        if not reaches:
            if policy_forks > 0 and not has_guards:
                findings.append(
                    SecurityFinding(
                        severity="high",
                        category="Policy Persistence",
                        message=(
                            f"{policy_forks} structural policy/tool forks (Δ) detected "
                            "with no explicit Stem (⊤) termination on one-way channels."
                        ),
                        recommendation=(
                            "Consider inserting explicit Stems on sensitive observation or "
                            "user-data paths after first use, or scoping policy copies to "
                            "narrower objects. Review any path where copied policy can reach "
                            "tool invocations alongside user data."
                        ),
                        evidence={"policy_forks": policy_forks, "stems": stems, "forks_by_type": forks_by},
                    )
                )
            elif policy_forks > 0 and has_guards:
                findings.append(
                    SecurityFinding(
                        severity="medium",
                        category="Policy Copying",
                        message=(
                            f"{policy_forks} policy/tool Δ forks present alongside {stems} explicit guards."
                        ),
                        recommendation=(
                            "Verify that guards (Stems) are placed on all sensitive one-way "
                            "channels. Policy copying is often legitimate; the risk is "
                            "unbounded lifetime for user data or secrets alongside it."
                        ),
                        evidence={"policy_forks": policy_forks, "stems": stems},
                    )
                )

        if policy_forks == 0 and raw.get("one_way_paths", 0) > 0:
            findings.append(
                SecurityFinding(
                    severity="low",
                    category="Information Flow",
                    message="Diagram contains only one-way paths with no policy copying.",
                    evidence={"one_way_paths": raw["one_way_paths"]},
                )
            )

        # Always useful classification note for serious reviews
        if forks_by or stems_by:
            findings.append(
                SecurityFinding(
                    severity="low",
                    category="Fork/Stem Classification",
                    message=f"Fork classification: {forks_by}. Stem classification: {stems_by}.",
                    evidence={"forks_by_type": forks_by, "stems_by_type": stems_by},
                    recommendation="Use the per-type counts to distinguish policy lifetime from transient user data lifetime.",
                )
            )

        # Risk aggregation
        if any(f.severity == "high" for f in findings):
            overall_risk: Literal["high", "medium", "low"] = "high"
            summary = (
                "High-risk geometry via path-sensitive analysis: sensitive one-way values reach "
                "tool contexts while policy copies are simultaneously live, with insufficient "
                "termination. Inspect raw_geometry['sensitive_reaches'] and ['flow_summary']."
            )
        elif any(f.severity == "medium" for f in findings):
            overall_risk = "medium"
            summary = (
                "Moderate risk: policy copying + explicit guards present. Path analysis shows "
                "sensitive values did reach contexts under policy influence; some channels were "
                "terminated by Stems. Review the concrete reaches for your specific threat model."
            )
        else:
            overall_risk = "low"
            summary = "No high-risk policy-copy + unguarded-sensitive co-flow patterns detected."

        return SecurityReport(
            title=title,
            summary=summary,
            overall_risk=overall_risk,
            findings=findings,
            raw_geometry=raw,
            metadata={
                "analyzer_version": "0.3",
                "analyzer_class": "SafetyAnalyzer",
                "features": ["path_sensitive_flow", "fork_classification", "sensitive_reachability", "guard_effect_tracking"],
            },
        )


def analyze_safety_geometry(diagram: StringDiagram | DiagramElement) -> dict[str, Any]:
    """
    Lightweight structural walk (upgraded implementation).

    Now powered by SafetyAnalyzer: path-sensitive flow tracking + fork classification
    in addition to the original counts. All original dict keys are still present with
    identical semantics for existing code; new keys provide the richer audit data.
    (Includes the illustrative "policy_copy_vs_sensitive_reach_summary" derived metric.)
    """
    analyzer = SafetyAnalyzer(diagram)
    return analyzer.analyze()


def generate_security_report(
    diagram: StringDiagram | DiagramElement,
    title: str | None = None,
) -> SecurityReport:
    """
    Produce an illustrative but now substantially more useful structured report.

    Delegates to SafetyAnalyzer.generate_report. The resulting SecurityReport
    (and its .findings + raw_geometry) is intended to be pasted into design reviews,
    PR comments, or red-team artifacts. Much less "canned text", much more
    "here is exactly which sensitive value reached which box under which fork".
    Raw geometry includes the illustrative policy_copy_vs_sensitive_reach_summary metric.
    """
    analyzer = SafetyAnalyzer(diagram)
    return analyzer.generate_report(title)
