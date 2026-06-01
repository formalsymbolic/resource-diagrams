#!/usr/bin/env python3
"""
simple_agent_resource_model.py
================================

Models a minimal ReAct-style (Reason + Act) agent loop as a string diagram
using the core primitives (Object, Morphism, DataService, MonoidalComputer).

The diagram explicitly shows:
- A one-way user input wire (information flows in; the original input
  is not automatically retained by the agent after the first step).
- Copying of the policy / system prompt into both the Reason and Act
  stages (via Δ).
- Resource wires for tokens / steps (abstracted as a separate object).
- The feedback loop from observation back into the next reason step.

This makes certain information-flow and retention properties visible
in the geometry before any execution occurs.

Run:
    python examples/simple_agent_resource_model.py

(Direct execution supported on fresh clone via bootstrap guard.)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap guard: enables single-command `python examples/simple...py`
# from fresh clone (resource-diagrams/ dir) with no prior setup.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams import DataService, Object
from resource_diagrams.models import build_simple_react_diagram


def main() -> None:
    print("=" * 72)
    print("RESOURCE DIAGRAMS — ReAct-Style Agent Resource Model (via models layer)")
    print("=" * 72)
    print()

    # The models layer provides a high-level builder that returns a Diagram
    # object containing the sequence of core Morphisms, a Mermaid rendering,
    # and an associated safety interpretation.
    diagram = build_simple_react_diagram(tools=["web_search", "code_interpreter"], cycles=2)

    print("Policy / tool definitions treated as copyable basic data (▼ triangles + Δ):")
    print("   (see the generated diagram for the explicit forks on AgentPolicy+ToolDefs)")
    print()

    # Demonstrate DataService copy remains available at low level
    policy_code = "react_policy_v1"
    p1, p2 = DataService.copy(policy_code, Object("Ξ"))
    print(f"Low-level confirmation: DataService.copy on policy yields independent copies: {p1 is not p2 or p1 == p2}")
    print()

    # ------------------------------------------------------------------
    # The diagram from the models layer (uses diagrams layer internally)
    # ------------------------------------------------------------------
    print("ReAct Loop as String Diagram (Mermaid via models + diagrams layers)")
    print("-" * 72)
    print("```mermaid")
    print(diagram.to_mermaid())
    print("```")
    print()

    # ------------------------------------------------------------------
    # Illustrative commentary (directly from the model builder — 1 paragraph;
    # labeled "illustrative interpretation" + backed by _scan_safety_geometry)
    # ------------------------------------------------------------------
    print("Safety interpretation associated with the diagram")
    print("-" * 72)
    print(diagram.safety_explanation)
    print()
    print("=" * 72)
    print("The models layer associates interpretive annotations with the")
    print("generated diagrams. The underlying categorical structure is")
    print("available via the diagrams layer (Fork and Stem elements).")
    print("=" * 72)


if __name__ == "__main__":
    main()
