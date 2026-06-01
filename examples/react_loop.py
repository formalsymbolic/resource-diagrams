#!/usr/bin/env python3
"""
examples/react_loop.py

Standalone runnable example of the models layer.

Builds a ReAct-style loop as a resource diagram using the high-level
builder from resource_diagrams.models. Prints Mermaid source (paste
into any renderer) plus the safety explanation (explicitly an
"illustrative interpretation" of the trace geometry + annotations per
addressing the gap between hardcoded and derived explanations; a lightweight scanner
provides the derivation basis from step program_code etc.).

ReAct-style loops with explicit resource accounting constitute one of the central modeling patterns developed in the models layer.

Run:
    python examples/react_loop.py

(From the resource-diagrams/ dir in a fresh clone; the guard below makes
this work with zero setup. The -m form does not apply as examples/ live
outside the installed package.)

All framing is authentic to the Resource Diagrams project (monoidal
categorical diagrammatic modeling for AI safety). No external agent
frameworks.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap guard (consistent across all examples): supports direct run
# `python examples/react_loop.py` from fresh clone (pre-install).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams.models import build_simple_react_diagram


def main() -> None:
    print("=" * 72)
    print("RESOURCE DIAGRAMS — ReAct Loop Modeling Example")
    print("Core modeling pattern: Tool-calling / ReAct-style loops as diagrams")
    print("=" * 72)
    print()

    tools = ["web_search", "calculator", "code_exec"]
    d = build_simple_react_diagram(tools=tools, cycles=2)

    print("Built diagram for a 2-cycle ReAct trace with 3 tools.")
    print("Underlying Morphism trace length:", len(d.steps))
    print()

    print("--- Mermaid source (copy-paste into GitHub / Mermaid Live / VS Code) ---")
    print()
    print(d.to_mermaid())
    print()

    print("--- Safety insight made visible by this diagram ---")
    print()
    print(d.safety_explanation)
    print()

    # Also demonstrate integration with diagrams layer
    sd = d.to_string_diagram()
    if sd is not None:
        print("Also available as diagrams.StringDiagram (for tensor/fork composition):")
        print(repr(sd))
        print("Its .to_mermaid() (via official renderer) length:", len(sd.to_mermaid()))
    else:
        print("(to_string_diagram() returned None in this env; lightweight Mermaid always works)")

    print()
    print("=" * 72)
    print("End of react_loop.py example. The diagram renders the exact asymmetry")
    print("between copyable policy/tool data (Δ) and one-way user/obs flow.")
    print("=" * 72)


if __name__ == "__main__":
    main()
