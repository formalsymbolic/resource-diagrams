#!/usr/bin/env python3
"""
fixed_point_demo.py
=====================

Demonstrates a simple fixed-point construction inspired by ideas in
Monoidal Computer Paper I.

This is an illustrative example in a symbolic model, not a rigorous
implementation of the theorem from the paper.

Run:
    python examples/fixed_point_demo.py

(From resource-diagrams/ checkout dir; works on fresh clone thanks to
the sys.path guard below.)

Supports --check-laws (for auditors, no pytest/hypothesis needed):

    python examples/fixed_point_demo.py --check-laws

Executes key checks from tests/paper_laws.py (fixed point laws for p_codes;
diagram geometry basics). Prints PASS/summary. All output/docstrings use
"within this symbolic model", "illustrative witness", "not a formal proof".
Nothing here is a formal proof.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Bootstrap for direct `python examples/fixed_point_demo.py` on fresh
# clone (no install/PYTHONPATH required). Uses src layout.
# We also put the checkout root on sys.path so that --check-laws can
# import the pure helpers from tests/paper_laws.py (no test runner needed).
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root))

from resource_diagrams import DataService, MonoidalComputer, Object


def run_law_checks() -> None:
    """Run key structural checks from tests/paper_laws.py (no pytest/hypothesis).

    Witnesses (within this symbolic model only; illustrative, not a formal proof):
      - programs_copy_to_identical_pairs (Paper I §6 axiom for fp diagrammatics)
      - phi_self_application_law (Lemma 6.2) for a few p_codes
      - fixed_point_construction_law (Prop 6.1 style) for a few p_codes
      - diagram_illustrates_paper_geometry for basic cases (tree + renderer)

    See module docstring for full disclaimers. Every result here is scoped to
    "within this symbolic model", "illustrative witness", "not a formal proof".
    """
    print("=" * 72)
    print("RESOURCE DIAGRAMS — Law Witnesses (in-model; from paper_laws.py)")
    print("=" * 72)
    print("WITHIN THIS SYMBOLIC MODEL only. ILLUSTRATIVE WITNESSES. NOT A FORMAL PROOF.")
    print("Re-runnable without pytest: PYTHONPATH=src python examples/fixed_point_demo.py --check-laws")
    print()

    try:
        from tests.paper_laws import (
            assert_diagram_illustrates_paper_geometry,
            assert_fixed_point_construction_law,
            assert_phi_self_application_law,
            assert_programs_copy_to_identical_pairs,
        )
        from resource_diagrams import XI
        from resource_diagrams.diagrams import (
            MermaidRenderer,
            StringDiagram,
            tensor,
            triangle,
            wire,
        )
    except Exception as exc:
        print(f"ERROR: cannot import paper_laws: {exc}")
        return

    failures = 0
    passes = 0

    def witness(name: str, fn, *args, **kwargs) -> None:
        nonlocal failures, passes
        try:
            fn(*args, **kwargs)
            print(f"PASS: {name}")
            passes += 1
        except AssertionError as ex:
            print(f"FAIL: {name}: {ex}")
            failures += 1
        except Exception as ex:
            print(f"ERROR: {name}: {type(ex).__name__}: {ex}")
            failures += 1

    print("--- fixed point law prerequisites / axioms ---")
    witness("programs_copy_to_identical_pairs(['id','succ','const0'])", assert_programs_copy_to_identical_pairs, ["id", "succ", "const0"])

    print("--- phi self-app law (Lemma 6.2) ---")
    mc = MonoidalComputer()
    for p in ["id", "succ", "const0"]:
        witness(f"phi_self_application({p!r})", assert_phi_self_application_law, mc, p)

    print("--- fixed point construction law (Prop 6.1) for a few p_codes ---")
    mc = MonoidalComputer()
    for p in ["id", "succ", "const0"]:
        witness(f"fixed_point_construction({p!r})", assert_fixed_point_construction_law, mc, p)

    print("--- diagram geometry (basic cases) ---")
    r = MermaidRenderer()
    frag = StringDiagram(tensor(triangle("p42", XI), wire(Object("L"))), title="eval_frag")
    witness("diagram_geometry(evaluator_fragment)", assert_diagram_illustrates_paper_geometry, frag, "evaluator law fragment")
    fp_mmd = r.render_fixed_point_construction("succ")
    witness("diagram_geometry(fixed_mmd)", assert_diagram_illustrates_paper_geometry, fp_mmd, "fixed point (Paper I)")

    total = passes + failures
    print()
    print("=" * 72)
    print(f"SUMMARY: {passes} PASS, {failures} FAIL ({total} witnesses)")
    print("All checks: WITHIN THIS SYMBOLIC MODEL. ILLUSTRATIVE WITNESSES. NOT A FORMAL PROOF.")
    print("=" * 72)
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Paper I fixed-point demo (+ --check-laws mode).")
    parser.add_argument("--check-laws", action="store_true", help="run key law witnesses from paper_laws.py (no pytest)")
    args = parser.parse_args()
    if args.check_laws:
        run_law_checks()
        return
    # original demo (unchanged when run without flag)
    print("=" * 72)
    print("RESOURCE DIAGRAMS — Fixed Point Construction Idea (Paper I p.26 style)")
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
    print("   Without this, the graphical construction below would not be possible.")
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
    print("4. The string diagram (Paper I p.26 style — fixed point via copying)")
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
    print("What the diagram illustrates")
    print("-" * 72)
    print(
        "The diagram illustrates the key mechanism in the paper's graphical\n"
        "argument for the existence of fixed points within the monoidal\n"
        "computer model. Because a universal evaluator u exists and\n"
        "because programs (elements of Ξ) are basic data under the data services\n"
        "(Δ, ⊤), any program p may be copied, with one copy supplied to u as\n"
        "the program argument and the other as the data argument, yielding {p}(p).\n\n"
        "The self-application transformer Φ composed in this way provides\n"
        "a diagrammatic handle on the fixed-point property. In the paper's\n"
        "notation, this corresponds to the construction of a q such that\n"
        "the meanings satisfy the fixed-point equation in the model.\n\n"
        "The construction yields one of the most transparent diagrammatic\n"
        "illustrations in the Monoidal Computer series and provides a\n"
        "visual aid for thinking about self-reference, recursion, and\n"
        "resource-bounded reasoning in this framework."
    )
    print()
    print("=" * 72)
    print("End of demonstration. The construction demonstrates the universal")
    print("evaluator and the data-service copy operation on basic data.")
    print("(within this symbolic model; illustrative; not a formal proof)")
    print("=" * 72)


if __name__ == "__main__":
    main()
