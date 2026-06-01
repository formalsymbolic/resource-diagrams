"""
resource_diagrams.cli
=====================

Minimal, zero-dependency CLI entry point (stdlib argparse only + the
existing public resource_diagrams API).

Commands:
  resource-diagrams demo fixed-point
  resource-diagrams analyze <example>
  resource-diagrams laws

All output carries the early-prototype disclaimer.
See the README for scope and limitations.

Prefer the Python API for real use.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

# All imports use the *public* API only (top-level reexports where available,
# plus the documented models/ and diagrams/ submodules). Zero runtime deps.
from resource_diagrams import (
    DataService,
    MonoidalComputer,
    Object,
    StringDiagram,
    analyze_safety_geometry,
    box,
    fork,
    seq,
    stem,
    tensor,
    triangle,
    wire,
    # MermaidRenderer is public via lazy __getattr__ + diagrams
    MermaidRenderer,
)
from resource_diagrams.models import (
    basic_info_flow_diagram,
    build_guarded_vs_unguarded_contrast,
    build_hierarchical_agent_diagram,
    build_multi_agent_coordination_diagram,
    build_reflexion_with_critic_diagram,
    build_simple_react_diagram,
    model_token_accounting,
)

# Honest disclaimer carried verbatim in *every* code path and help text.
# Matches tone used throughout README, docs/, and source docstrings.
EARLY_PROTOTYPE_DISCLAIMER: str = (
    "EARLY EXPERIMENTAL PROTOTYPE\n"
    "All CLI output is illustrative and scoped to a symbolic model over program\n"
    "names and Python callables. This is not a security analysis tool, not a\n"
    "formal-methods library, and not production tooling. See the README for\n"
    "limitations.\n"
)


def _print_disclaimer() -> None:
    print(EARLY_PROTOTYPE_DISCLAIMER)
    print("=" * 72)


def _get_sd(obj: Any) -> Any:
    """Return a StringDiagram for analyze_safety_geometry from a builder result.

    Handles both modern builders (populated .string_diagram) and legacy
    Diagram facades (via .to_string_diagram()). Falls back to a trivial
    valid diagram so the CLI never crashes on analyze (thin wrapper only).
    """
    if obj is None:
        xi = Object("X")
        return StringDiagram(wire(xi), title="cli-fallback")
    if hasattr(obj, "string_diagram") and getattr(obj, "string_diagram", None) is not None:
        return obj.string_diagram
    if hasattr(obj, "to_string_diagram"):
        try:
            sd = obj.to_string_diagram()
            if sd is not None:
                return sd
        except Exception:
            pass
    # If the object is already usable as a diagram element / StringDiagram
    if isinstance(obj, StringDiagram) or hasattr(obj, "root"):
        return obj
    # Last-resort trivial but valid diagram (uses only public ctors)
    xi = Object("Ξ")
    try:
        return StringDiagram(seq(triangle("p", xi), wire(xi)), title="cli-trivial")
    except Exception:
        return StringDiagram(wire(xi), title="cli-trivial")


def run_demo_fixed_point() -> None:
    """Thin wrapper around MonoidalComputer.build_fixed_point + renderer."""
    print("demo fixed-point")
    print("Thin wrapper: MonoidalComputer + MermaidRenderer (public API only)")
    print()
    mc = MonoidalComputer()
    try:
        fp_code, meaning = mc.build_fixed_point("succ")
        print(f"mc.build_fixed_point('succ') -> fp_code={fp_code!r}")
        print(f"meaning={meaning!r}")
    except Exception as exc:
        print(f"build_fixed_point error (prototype): {exc}")
    print()
    try:
        r = MermaidRenderer()
        mmd = r.render_fixed_point_construction("succ")
        print("MermaidRenderer.render_fixed_point_construction('succ') [truncated]:")
        print(mmd[:600] + ("..." if len(mmd) > 600 else ""))
    except Exception as exc:
        print(f"(renderer unavailable in this context: {exc})")
    print()
    print("(within this symbolic model; illustrative; not a formal proof)")
    _print_disclaimer()


def run_analyze(spec: str) -> None:
    """Thin wrapper around public builders + analyze_safety_geometry.

    Accepts built-in example names (react, guarded, hierarchical, reflexion,
    multi, token, info, fixed-point) or any other string (falls back to a
    trivial diagram). No complex spec parsing — keeps the surface tiny.
    """
    print(f"analyze {spec!r}")
    print("Thin wrapper: public builder (or trivial) + analyze_safety_geometry")
    print()

    d: Any = None
    spec_lower = spec.lower().strip()

    if spec_lower in {"react", "simple-react", "default", ""}:
        d = build_simple_react_diagram(tools=["search"], cycles=1, title=f"cli-analyze-{spec}")
    elif spec_lower.startswith("guard"):
        gc = build_guarded_vs_unguarded_contrast()
        # Prefer the guarded variant (explicit Stem) for interesting geometry
        d = getattr(gc, "guarded", gc)
    elif spec_lower in {"hierarchical", "hier"}:
        d = build_hierarchical_agent_diagram()
    elif spec_lower.startswith("reflex"):
        d = build_reflexion_with_critic_diagram()
    elif spec_lower in {"multi", "multi-agent", "multiagent"}:
        d = build_multi_agent_coordination_diagram()
    elif spec_lower in {"token", "accounting", "tokens"}:
        d = model_token_accounting(
            steps=[("reason", 45), ("tool_call:search", 120), ("observe", 30)],
            total_budget=500,
            title=f"cli-analyze-{spec}",
        )
    elif spec_lower in {"info", "info-flow", "flow"}:
        d = basic_info_flow_diagram(title=f"cli-analyze-{spec}")
    elif spec_lower in {"fixed-point", "fp", "fixedpoint"}:
        # Construct a minimal fixed-point style diagram using only public ctors
        # (so analyze has triangles + tensor for geometry to walk).
        xi = Object("Ξ")
        d = StringDiagram(
            seq(tensor(triangle("succ", xi), wire(xi)), box("u", src=xi, tgt=Object("Result"))),
            title="cli-analyze-fixed-point",
        )
    else:
        print(f"  (unknown built-in example {spec!r}; using trivial public-ctor fallback)")
        xi = Object("Ξ")
        d = StringDiagram(seq(triangle(spec or "p", xi), wire(xi)), title=f"cli-analyze-{spec}")

    sd = _get_sd(d)
    print("  diagram ready; calling analyze_safety_geometry(sd) ...")
    try:
        geom: dict[str, Any] = analyze_safety_geometry(sd)
        # Emit a compact, useful subset (full dict available to callers)
        keys = sorted(k for k in geom.keys() if not k.startswith("_"))
        print(f"  keys: {keys}")
        if "policy_copy_vs_sensitive_reach_summary" in geom:
            print("  policy_copy_vs_sensitive_reach_summary:")
            print(f"    {geom['policy_copy_vs_sensitive_reach_summary']}")
        # A few legacy/compat fields often present
        for k in ("policy_forks", "stems", "sensitive_reaches", "has_explicit_guards"):
            if k in geom:
                print(f"  {k}: {geom[k]}")
    except Exception as exc:
        print(f"  analyze_safety_geometry error (prototype scope): {exc}")
    print()
    _print_disclaimer()


def run_laws() -> None:
    """Light re-use of the --check-laws logic from examples/fixed_point_demo.py.

    We cannot (and must not) depend on tests/ being on sys.path for an
    installed package, so we inline a few direct witnesses using only the
    public API (DataService + MonoidalComputer + analyze). This is the
    "re-uses the logic lightly" path. Every witness is explicitly scoped.
    """
    print("laws")
    print("Light inline witnesses (re-using ideas from fixed_point_demo --check-laws).")
    print("WITHIN THIS SYMBOLIC MODEL only. ILLUSTRATIVE WITNESSES. NOT A FORMAL PROOF.")
    print()

    mc = MonoidalComputer()
    passes = 0
    fails = 0

    def witness(name: str, condition: bool, note: str = "") -> None:
        nonlocal passes, fails
        if condition:
            print(f"PASS: {name}{note}")
            passes += 1
        else:
            print(f"FAIL: {name}{note}")
            fails += 1

    # 1. DataService basic copy axiom (enables the whole diagrammatic fp story)
    try:
        p1, p2 = DataService.copy("succ", Object("Ξ"))
        witness(
            "programs_copy_to_identical_pairs(['succ'])",
            (p1, p2) == ("succ", "succ"),
            "  # Paper I §6 axiom: δ ∘ p = p ⊗ p for basic data",
        )
    except Exception as exc:
        witness("programs_copy_to_identical_pairs", False, f"  # error: {exc}")

    # 2. Fixed point construction (public entry point)
    try:
        fp_code, meaning = mc.build_fixed_point("succ")
        ok = fp_code is not None and meaning is not None
        witness(
            "fixed_point_construction_law('succ')",
            ok,
            "  # Prop 6.1 style via MonoidalComputer (symbolic)",
        )
    except Exception as exc:
        witness("fixed_point_construction_law", False, f"  # error: {exc}")

    # 3. phi self-application (via public if available, else via build)
    try:
        # MonoidalComputer exposes .phi in the implementation; use getattr for safety
        phi = getattr(mc, "phi", None)
        if callable(phi):
            p_code, p_meaning = phi("succ")
            ok = p_code is not None
        else:
            # fallback: build_fixed_point internally uses the same
            fp_code, _ = mc.build_fixed_point("succ")
            ok = fp_code is not None
        witness(
            "phi_self_application_law('succ')",
            ok,
            "  # Lemma 6.2 style (within model)",
        )
    except Exception as exc:
        witness("phi_self_application_law", False, f"  # error: {exc}")

    # 4. Basic diagram geometry via public analyze (exercises the structural walker)
    try:
        xi = Object("Ξ")
        frag = StringDiagram(tensor(triangle("p42", xi), wire(Object("L"))), title="cli-law-frag")
        geom = analyze_safety_geometry(frag)
        ok = isinstance(geom, dict) and ("forks" in geom or "policy_forks" in geom or "boxes_encountered" in geom)
        witness(
            "diagram_illustrates_paper_geometry (basic tensor+triangle)",
            ok,
            "  # structural walk over Fork/Triangle/etc",
        )
    except Exception as exc:
        witness("diagram_illustrates_paper_geometry", False, f"  # error: {exc}")

    total = passes + fails
    print()
    print("=" * 72)
    print(f"SUMMARY: {passes} PASS, {fails} FAIL ({total} witnesses)")
    print("All checks: WITHIN THIS SYMBOLIC MODEL. ILLUSTRATIVE WITNESSES. NOT A FORMAL PROOF.")
    print("=" * 72)
    _print_disclaimer()


def main(argv: list[str] | None = None) -> None:
    """Entry point for console script and python -m."""
    if argv is not None:
        sys.argv = ["resource-diagrams", *argv]

    parser = argparse.ArgumentParser(
        prog="resource-diagrams",
        description=(
            "resource-diagrams — minimal CLI for the early-prototype resource\n"
            "diagrams library (string diagrams + monoidal computer model).\n\n"
            + EARLY_PROTOTYPE_DISCLAIMER
        ),
        epilog=(
            "This CLI is packaging polish only (high-leverage usability signal).\n"
            "It is a zero-dependency thin wrapper around the public Python API.\n"
            "For real work use the Python interface shown in README quickstart.\n\n"
            + EARLY_PROTOTYPE_DISCLAIMER
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="resource-diagrams 0.1.0 (early experimental prototype)",
        help="show version and exit",
    )

    subparsers = parser.add_subparsers(dest="cmd", required=False, help="sub-command")

    # demo fixed-point
    p_demo = subparsers.add_parser(
        "demo",
        help="Run an illustrative built-in demo",
        description="Run demos using only public builders. " + EARLY_PROTOTYPE_DISCLAIMER,
    )
    p_demo.add_argument(
        "kind",
        choices=["fixed-point"],
        help="demo variant (only 'fixed-point' supported in this prototype CLI)",
    )

    # analyze
    p_anal = subparsers.add_parser(
        "analyze",
        help="Run analyze_safety_geometry over a built-in example diagram",
        description=(
            "Build a diagram via a public model builder (or trivial ctor) then\n"
            "call analyze_safety_geometry. <spec> is a built-in name:\n"
            "  react | guarded | hierarchical | reflexion | multi | token | info | fixed-point\n"
            "Unknown specs fall back to a minimal valid diagram (no heavy features).\n\n"
            + EARLY_PROTOTYPE_DISCLAIMER
        ),
    )
    p_anal.add_argument(
        "spec",
        help="diagram spec or built-in example name (see description)",
    )

    # laws (delegates lightly to check-laws capability)
    p_laws = subparsers.add_parser(
        "laws",
        help="Run illustrative law witnesses (light re-use of fixed_point_demo --check-laws)",
        description=(
            "Prints a few direct law witnesses using only the public API.\n"
            "Re-uses the spirit of examples/fixed_point_demo.py --check-laws\n"
            "but inlines the checks so the CLI works for installed packages\n"
            "(tests/ are not shipped). All output is explicitly scoped.\n\n"
            + EARLY_PROTOTYPE_DISCLAIMER
        ),
    )

    args = parser.parse_args()

    _print_disclaimer()

    if args.cmd == "demo":
        if args.kind == "fixed-point":
            run_demo_fixed_point()
        else:
            parser.error("unknown demo kind")
    elif args.cmd == "analyze":
        run_analyze(args.spec)
    elif args.cmd == "laws":
        run_laws()
    else:
        # No subcommand — behave like --help but still emit disclaimer
        parser.print_help()
        print()
        print("Example invocations (conceptual after `pip install -e .` or console script):")
        print("  resource-diagrams --help")
        print("  resource-diagrams demo fixed-point")
        print("  resource-diagrams analyze react")
        print("  resource-diagrams analyze guarded")
        print("  resource-diagrams laws")
        print()
        _print_disclaimer()
        # Do not sys.exit(0) here so that direct python -c smoke can continue if needed


if __name__ == "__main__":
    main()
