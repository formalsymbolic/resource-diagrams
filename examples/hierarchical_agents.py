#!/usr/bin/env python3
"""
Hierarchical / nested agent structures as resource diagram.

Demonstrates the new modeling pattern where *inner agents are first-class
resources*: their policies are explicit program triangles (▼) that the
supervisor diagram can copy (Δ) or use linearly (with Stem after delegation).

This extends beyond flat ReAct or simple reflexion by making the "agent"
itself copyable data, with nested policy lifetimes (supervisor forks +
sub-policy forks) visible in one structural diagram.

Run:
    python examples/hierarchical_agents.py

Produces high-quality Mermaid (via StringDiagram + MermaidRenderer) and
full analyzer output (path-sensitive influence + fork classification by
type, showing subpolicy vs top policy forks).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams.diagrams.safety import analyze_safety_geometry, generate_security_report
from resource_diagrams.models import build_hierarchical_agent_diagram


def main() -> None:
    print("=" * 72)
    print("RESOURCE DIAGRAMS — Hierarchical/Nested Agent Pattern (NEW)")
    print("=" * 72)
    print()

    d = build_hierarchical_agent_diagram(
        subagent_names=["research_sub", "code_sub"],
        supervisor_name="SupervisorPolicy",
    )

    print("Diagram title:", d.title)
    print()
    print("Mermaid (clean structural rendering with Δ/⊤ geometry):")
    mmd = d.to_mermaid()
    print(mmd)
    print()

    # Save for gallery / exports (like other examples)
    exports_dir = Path(__file__).resolve().parents[1] / "examples" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    out_path = exports_dir / "07_hierarchical_nested_agents.mmd"
    out_path.write_text(mmd, encoding="utf-8")
    print(f"Saved: {out_path}")
    print()

    print("--- safety_explanation (illustrative of the new geometry) ---")
    print(d.safety_explanation)
    print()

    # Full analyzer (now has subpolicy forks classified under policy type,
    # stems on SubObservation and on the SubAgentPolicy_* resources themselves)
    if d.string_diagram is not None:
        analysis = analyze_safety_geometry(d.string_diagram)
        print("--- analyze_safety_geometry (structural, path-sensitive) ---")
        print(analysis)
        print()

        report = generate_security_report(d.string_diagram, title="Hierarchical Agent Review")
        print("--- generate_security_report summary ---")
        print("overall_risk:", report.overall_risk)
        for f in report.findings[:3]:
            print(f"  {f.severity}: {f.category}: {f.message[:120]}...")
        print()

    print("Key non-trivial aspects of this pattern:")
    print("- SubAgentPolicy_* triangles are resources that appear in the entry tensor.")
    print("- First sub uses explicit fork(Δ) on its policy obj (copied sub-agent).")
    print("- Stems after each sub bound both the sub-obs *and* the sub-policy copy.")
    print("- Analyzer distinguishes forks_by_type (multiple 'policy' entries for sup+subs).")
    print("- This models agent spawning / sub-policy exfiltration surfaces defensibly.")
    print()
    print("=" * 72)
    print("hierarchical_agents.py complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()
