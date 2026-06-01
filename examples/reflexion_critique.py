#!/usr/bin/env python3
"""
Explicit reflexion / self-critique loop with separate critic policy fork
and resource accounting.

This provides a fully structural realization of a Reflexion-style critic pattern using explicit policy resources and termination boundaries.

- Actor: own policy triangle + Δ forks + ReAct-style steps + one-way obs.
- Boundary: dedicated one-way "ActorObservationToCritic" wire (no Δ).
- Critic: *separate* "CriticPolicy" triangle + its own independent Δ fork.
- Accounting: critique step annotated with explicit token cost in its label/
  program_code; stems terminate the critic's sensitive input and revision output.
- Feedback: linear "ApplyCriticRevision" back (no auto Δ of critic output).

The resulting diagram + analyzer makes the "critic tax" (second copied policy
+ extra compute) and the one-way info boundary between actor and critic
visible and countable. Useful for Reflexion, debate, constitutional critique.

Run:
    python examples/reflexion_critique.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams.diagrams.safety import analyze_safety_geometry
from resource_diagrams.models import build_reflexion_with_critic_diagram


def main() -> None:
    print("=" * 72)
    print("RESOURCE DIAGRAMS — Reflexion/Self-Critique with Explicit Critic Fork + Accounting (NEW)")
    print("=" * 72)
    print()

    d = build_reflexion_with_critic_diagram(
        tools=["search", "calculator"],
        cycles=1,
    )

    print("Diagram title:", d.title)
    print()
    mmd = d.to_mermaid()
    print("Mermaid (actor spine ; one-way critic entry ; separate critic Δ ; stems):")
    print(mmd)
    print()

    exports_dir = Path(__file__).resolve().parents[1] / "examples" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    out_path = exports_dir / "08_reflexion_critic_policy.mmd"
    out_path.write_text(mmd, encoding="utf-8")
    print(f"Saved: {out_path}")
    print()

    print("--- safety_explanation ---")
    print(d.safety_explanation)
    print()

    if d.string_diagram is not None:
        analysis = analyze_safety_geometry(d.string_diagram)
        print("--- analyze_safety_geometry ---")
        # Highlight the interesting bits for this pattern (includes illustrative structural metric)
        print({
            k: analysis[k]
            for k in (
                "policy_forks",
                "stems",
                "forks_by_type",
                "stems_by_type",
                "sensitive_reaches",
                "flow_summary",
                "policy_copy_vs_sensitive_reach_summary",
            )
            if k in analysis
        })
        print()

    print("Key non-trivial aspects:")
    print("- Two distinct policy triangles/forks: ActorPolicy vs CriticPolicy.")
    print("- One-way boundary wire (ActorObservationToCritic) carries sensitive into critic scope.")
    print("- Critic step cost explicit; stems on critic_in and revision bound persistence.")
    print("- Analyzer will show policy forks + co-flow of the actor obs under (at least) critic copy.")
    print("- Directly accounts for the extra resource surface of self-critique loops.")
    print()
    print("=" * 72)
    print("reflexion_critique.py complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()
