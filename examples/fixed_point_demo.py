#!/usr/bin/env python3
"""
fixed_point_demo.py
=====================

Reproduces the central fixed-point construction from Monoidal Computer I
(Paper I, Lemma 6.2 and Proposition 6.1, p.25–26) using the library.

The construction shows that *every computation has a fixed point* via a
purely diagrammatic argument that relies on treating programs as basic
data that can be freely copied.

Run:
    python examples/fixed_point_demo.py

(From resource-diagrams/ checkout dir; works on fresh clone thanks to
the sys.path guard below. After `pip install -e ".[dev]"` the guard is
harmless and `python examples/...` continues to work.)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap for direct `python examples/fixed_point_demo.py` on fresh
# clone (no install/PYTHONPATH required). Uses src layout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams import DataService, MonoidalComputer, Object
from resource_diagrams.diagrams import MermaidRenderer


def main() -> None:
    print("=" * 72)
    print("RESOURCE DIAGRAMS — Fixed Point Construction (Paper I p.26)")
    print("=" * 72)
    print()

    mc = MonoidalComputer()

    # ------------------------------------------------------------------
    # Step 1: Programs as basic data (the crucial axiom)
    # ------------------------------------------------------------------
    print("1. Programs are basic data and therefore freely copyable")
    print("-" * 72)
    program = "succ"  # a simple program in the registry
    p1, p2 = DataService.copy(program, Object("Ξ"))
    print(f"   copy({program!r}, Ξ)  →  ({p1!r}, {p2!r})")
    print("   This is δ ∘ p = p ⊗ p  (the data-service axiom for basic data).")
    print("   Without this, the graphical proof below would not be possible.")
    print()

    # ------------------------------------------------------------------
    # Step 2: The self-application transformer Φ
    # ------------------------------------------------------------------
    print("2. The self-application transformer Φ (built from Δ + u)")
    print("-" * 72)
    phi_result = mc.apply("phi", program)
    print(f"   apply('phi', {program!r})  →  {phi_result!r}")
    print("   By definition, {Φ}(p) = {p}(p)   (one copy of p used as program,")
    print("                                   the other copy used as input data)")
    print()

    # ------------------------------------------------------------------
    # Step 3: The fixed-point construction itself
    # ------------------------------------------------------------------
    print("3. Fixed-point construction via build_fixed_point (central result)")
    print("-" * 72)
    fp_code, fp_meaning = mc.build_fixed_point(program)
    print(f"   build_fixed_point({program!r})  →  code={fp_code!r}, meaning={fp_meaning!r}")
    print()

    # ------------------------------------------------------------------
    # Step 4: The string diagram — now generated live via the diagrams layer
    # ------------------------------------------------------------------
    print("4. The string diagram (Paper I, p.26 — fixed point via copying)")
    print("   (rendered programmatically by MermaidRenderer.render_fixed_point_construction)")
    print("-" * 72)
    print()

    renderer = MermaidRenderer()
    fp_mmd = renderer.render_fixed_point_construction("succ")
    print("```mermaid")
    print(fp_mmd)
    print("```")
    print()

    # Also show construction trace from the MonoidalComputer (auditability)
    print("Construction trace (from MonoidalComputer):")
    print(mc.get_construction_trace())
    print()

    # ------------------------------------------------------------------
    # What the diagram proves (commentary for the reader)
    # ------------------------------------------------------------------
    print("What the diagram proves")
    print("-" * 72)
    print(
        "The diagram constitutes a proof of the recursion theorem within the\n"
        "monoidal computer model. Because a universal evaluator u exists and\n"
        "because programs (elements of Ξ) are basic data under the data services\n"
        "(Δ, ⊤), any program p may be copied, with one copy supplied to u as\n"
        "the program argument and the other as the data argument, yielding {p}(p).\n\n"
        "Composition of the resulting self-application transformer Φ with p\n"
        "itself produces a program q = Φ ; p whose meaning satisfies the\n"
        "fixed-point equation:\n\n"
        "    {q} = {p} ∘ {q}\n\n"
        "Equivalently, the behavior of q on an arbitrary input coincides with\n"
        "the result of first executing q on that input and then applying the\n"
        "original computation p to the outcome. The complete argument is\n"
        "embodied in the geometry of the string diagram; no auxiliary encoding\n"
        "or classical diagonal lemma is required.\n\n"
        "The construction yields one of the most transparent diagrammatic\n"
        "demonstrations in the Monoidal Computer series and provides a\n"
        "foundation for subsequent developments concerning self-reference,\n"
        "recursion, and resource-bounded reasoning."
    )
    print()
    print("=" * 72)
    print("End of demonstration. The construction follows from the universal")
    print("evaluator and the data-service copy operation on basic data.")
    print("=" * 72)


if __name__ == "__main__":
    main()
