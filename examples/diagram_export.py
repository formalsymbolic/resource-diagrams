#!/usr/bin/env python3
"""
diagram_export.py
==================

Builds several key string diagrams from the Monoidal Computer papers
programmatically (as Mermaid source) and exports them as .mmd files.

This demonstrates the "diagrams layer" usage pattern: diagrams are first-class
Python objects (here, simple string builders) that can be composed, parameterized,
and written to disk for use in papers, notebooks, or documentation.

The generated files are high-quality programmatic reconstructions of the
diagrammatic structures from the figures in the original papers and can be
rendered directly in GitHub, VS Code, Obsidian, etc. (They follow the visual
style and layout of the source figures but are not byte-identical.)

Run:
    python examples/diagram_export.py

(Works from a fresh clone with no install or PYTHONPATH, thanks to
bootstrap guard below. The script (re)generates the four
canonical paper figures (01-04) under examples/exports/ using the
diagrams layer, in the style of the source figures. See README for provenance of the AI model diagrams
05/06 which are snapshots from models-layer examples.)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap: allow `python examples/diagram_export.py` to work on fresh
# clone (before any `pip install -e .`) by adding src/ to path.
# Harmless after editable install too.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams import Object
from resource_diagrams.core import XI
from resource_diagrams.diagrams import (
    MermaidRenderer,
    StringDiagram,
    box,
    seq,
    tensor,
    triangle,
    wire,
)


def build_paper_figures_via_renderer(renderer: MermaidRenderer) -> dict[str, str]:
    """Use the delivered diagrams layer (MermaidRenderer) to produce the
    four canonical paper figures. These are generated live, not copied
    from static files. (The AI model diagrams 05/06 in exports/ come from
    the models layer examples and are committed as snapshots.)
    """
    return {
        "01_basic_string_diagrams": renderer.render_basic_monoidal("f", "g"),
        "02_universal_evaluator_law": renderer.render_evaluator_law("my_program"),
        "03_fixed_point_construction": renderer.render_fixed_point_construction("succ"),
        "04_data_services_comonoid": renderer.render_data_service_comonoid(),
    }


def build_one_string_diagram_programmatically() -> StringDiagram:
    """Example of building a tiny diagram tree from the element constructors
    (the 'programmatic' side of the diagrams layer) and wrapping it.
    """
    # A tiny evaluator-law fragment: (triangle p ⊗ wire(L)) ; box(u)
    p_tri = triangle("p", XI)
    l_wire = wire(Object("L"))
    u_box = box("u^L_M", src=XI, tgt=Object("M"))
    composed = seq(tensor(p_tri, l_wire), u_box)
    return StringDiagram(composed, title="programmatic_evaluator_fragment")


def main() -> None:
    print("=" * 72)
    print("RESOURCE DIAGRAMS — Programmatic Diagram Export (via diagrams layer)")
    print("=" * 72)
    print()

    renderer = MermaidRenderer()

    # Build the canonical paper figures using the renderer (in the style of 01-04)
    diagrams = build_paper_figures_via_renderer(renderer)

    # Demonstrate (but do not auto-write to exports/ to keep dir clean)
    # a tiny programmatic tree via the element constructors.
    programmatic_diag = build_one_string_diagram_programmatically()

    # Ensure export directory exists (the script itself creates it)
    export_dir = Path(__file__).parent / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    print(f"Exporting {len(diagrams)} diagrams (the four canonical paper figures) to {export_dir} ...")
    print()

    for name, content in diagrams.items():
        out_path = export_dir / f"{name}.mmd"
        out_path.write_text(content, encoding="utf-8")
        print(f"  ✓ {name}.mmd  ({len(content)} chars)")

    print()
    print("All diagrams written (the 01-04 paper figures in diagrammatic style). You can now:")
    print(f"  - Open any file in {export_dir} in a Mermaid-capable viewer")
    print("  - Embed them in Markdown with ```mermaid ... ```")
    print("  - Use them as starting points for further composition")
    print("  - (05/06 AI model diagrams are separate committed snapshots; see")
    print("    react_loop.py, simple_agent_resource_model.py etc for their source)")
    print()

    # Show one example inline (the fixed point one, abbreviated)
    print("Example inline (03_fixed_point_construction.mmd, first 12 lines):")
    print("-" * 72)
    lines = diagrams["03_fixed_point_construction"].splitlines()[:12]
    for line in lines:
        print(line)
    print("...")
    print()

    # Demonstrate programmatic tree roundtrip
    print("Programmatic StringDiagram example (to_text):")
    print(programmatic_diag.to_text())
    print()

    # Demonstrate that the core library objects can be used to parameterize
    xi = Object("Ξ")
    print(f"Library Object used for parameterization example: {xi}")
    print()

    print("=" * 72)
    print("Diagram export complete. The four paper figures (01-04) under")
    print("exports/ are ready for papers, talks, notebooks, documentation.")
    print("All generated via the diagrams layer (MermaidRenderer specialized).")
    print("See top of file and package README for 05/06 provenance.")
    print("=" * 72)


if __name__ == "__main__":
    main()
