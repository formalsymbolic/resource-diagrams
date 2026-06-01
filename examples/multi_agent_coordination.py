#!/usr/bin/env python3
"""
Multi-agent coordination patterns with explicit information flow boundaries.

Models two (or more) agents that:
- Have fully private policies (separate triangles; Δ on one does not
  duplicate the other agent's policy).
- Have private thought channels that are *stemmed* after local work
  (enforces isolation; no automatic leakage).
- May share a blackboard (Δ-copyable SharedBlackboard that each "reads"
  via explicit fork at access time).
- Coordinate only via an explicit ConsensusMerge box (the controlled
  crossing point; the merge rule itself may be a copyable policy).
- After merge, optional broadcast fork back to shared, then final stem.

Shared (Δ on blackboard) vs private (no fork on PrivateThought_*, stems) is
the core diagrammatic distinction. The analyzer quantifies boundary
effectiveness (does any private infl reach the merge? how many stems?).

This is the structural counterpart to informal "blackboard architectures",
"agent debate", "mixture-of-agents with private CoT + public vote", etc.

Run:
    python examples/multi_agent_coordination.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams.diagrams.safety import analyze_safety_geometry
from resource_diagrams.models import build_multi_agent_coordination_diagram


def main() -> None:
    print("=" * 72)
    print("RESOURCE DIAGRAMS — Multi-Agent Coordination (Private vs Shared + Explicit Merge) (NEW)")
    print("=" * 72)
    print()

    d = build_multi_agent_coordination_diagram(
        agent_names=["AgentA", "AgentB"],
        use_shared_blackboard=True,
    )

    print("Diagram title:", d.title)
    print()
    mmd = d.to_mermaid()
    print("Mermaid (private policies; shared Δ at access; private stems; merge; final shared stem):")
    print(mmd)
    print()

    exports_dir = Path(__file__).resolve().parents[1] / "examples" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    out_path = exports_dir / "09_multi_agent_coordination.mmd"
    out_path.write_text(mmd, encoding="utf-8")
    print(f"Saved: {out_path}")
    print()

    print("--- safety_explanation ---")
    print(d.safety_explanation)
    print()

    if d.string_diagram is not None:
        analysis = analyze_safety_geometry(d.string_diagram)
        print("--- analyze_safety_geometry (note forks_by_type for shared 'context' vs private) ---")
        print({
            k: analysis[k]
            for k in (
                "policy_forks",
                "stems",
                "forks_by_type",
                "stems_by_type",
                "sensitive_reaches",
                "flow_summary",
                "one_way_paths",
            )
            if k in analysis
        })
        print()

    print("Key non-trivial aspects of this pattern:")
    print("- Distinct policy objs per agent => independent forks (no cross-policy Δ).")
    print("- SharedBlackboard forks appear under 'context' (or policy if named so); privates under sensitive with stems.")
    print("- The ConsensusMerge is the *only* place private proposals can influence joint result.")
    print("- Stems on privates + final stem on shared make lifetime of each surface explicit.")
    print("- Analyzer flow_summary + reaches let a reviewer inspect exactly what crossed the boundary.")
    print()
    print("=" * 72)
    print("multi_agent_coordination.py complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()
