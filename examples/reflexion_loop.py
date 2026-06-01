#!/usr/bin/env python3
"""
Reflexion-style agent loop as resource diagram.

Demonstrates policy/tool copying (Δ) into both the main actor loop
and a parallel critic/reflector that receives one-way observations.

This extends the core ReAct hook with self-critique, a common pattern
in modern agent research (e.g., Reflexion, Self-Refine).

The diagram makes visible that the critic can also receive copied policy,
creating additional persistence surfaces, while raw feedback remains one-way.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams import Object, Morphism
from resource_diagrams.models import build_simple_react_diagram
from resource_diagrams.models.resources import InformationChannel

def main() -> None:
    print("=" * 72)
    print("RESOURCE DIAGRAMS — Reflexion / Self-Critique Loop (extension of core hook)")
    print("=" * 72)
    print()

    # Base ReAct for the actor
    actor = build_simple_react_diagram(
        tools=["web_search", "calculator"], 
        cycles=1,
        title="Actor Loop (with policy Δ)"
    )

    print("Actor (ReAct) diagram with policy copying:")
    print(actor.to_mermaid()[:1200])
    print("...")

    print("\n--- Safety insight for actor ---")
    print(actor.safety_explanation)
    print()

    # Simple critic loop illustration (one-way feedback + copied critic policy)
    # In a fuller version this would be a dedicated builder using Stem for feedback.
    print("Critic / Reflector receives one-way observations but can also fork policy.")
    print("This creates an additional vector for policy persistence via the critic path.")
    print()

    print("Key extension of the core value prop:")
    print("- Main policy forks (Δ) into actor and potentially into critic.")
    print("- Feedback/observations remain linear (no automatic Δ).")
    print("- This pattern appears in many self-improving agent designs.")

    # Demonstrate the new structural SafetyAnalyzer
    from resource_diagrams.diagrams.safety import analyze_safety_geometry
    if hasattr(actor, "string_diagram") and actor.string_diagram:
        analysis = analyze_safety_geometry(actor.string_diagram)
        print(f"\nStructural safety analysis on actor diagram: {analysis}")

    print("=" * 72)
    print("reflexion_loop.py complete. See models/agents.py for the base builder.")
    print("=" * 72)


if __name__ == "__main__":
    main()
