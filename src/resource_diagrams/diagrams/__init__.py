"""
diagrams — String diagram construction and high-quality Mermaid rendering.

This submodule provides an ergonomic programmatic API for building and
exporting the string diagrams that are the primary interface of the
Monoidal Computer framework (Pavlovic et al.). It is the top layer in the
architecture and the key deliverable for "String diagram construction +
high-quality Mermaid export".

Core abstractions (mirror categorical structure exactly):
- Wire / Object  → wires carrying data types
- Box / Morphism → processes, agent steps, tool calls, evaluators
- Triangle       → programs-as-data (▼ p)
- Fork (Δ) / Stem (⊤) → data service comonoid operations
- Sequential (;) / Tensor (⊗) → the two composition modes

Primary renderer: MermaidRenderer — produces GitHub-ready .mmd that
faithfully reproduces or strictly generalizes the four canonical paper
figures (see diagrams/01_*.mmd etc at repo root) without duplicating
their static content.

Exports are also available at the package top level after:
    from resource_diagrams import diagrams
or
    from resource_diagrams.diagrams import StringDiagram, MermaidRenderer, ...

All output uses pure research framing.

Typical usage (programmatic construction + export):

# New in recent expansion: lightweight structural safety analysis
from .safety import analyze_safety_geometry

__all__ = [
    "StringDiagram",
    "MermaidRenderer",
    "analyze_safety_geometry",
    "wire",
    "box",
    "triangle",
    "fork",
    "stem",
    "seq",
    "tensor",
    "from_morphism",
]

# Re-exports for convenience
from .diagram import (
    StringDiagram,
    MermaidRenderer,
    wire,
    box,
    triangle,
    fork,
    stem,
    seq,
    tensor,
    from_morphism,
)

from resource_diagrams import Object, Morphism

# Example (for documentation):
#   from resource_diagrams.diagrams import StringDiagram, from_morphism
#   # ... see README and notebooks for full usage

    # 3. Reproduce the exact fixed-point diagram (central result of Paper I §6) from Python
    renderer = MermaidRenderer()
    mmd = renderer.render_fixed_point_construction("my_agent_policy")
    print(mmd)                    # paste into GitHub
    # diag = StringDiagram( ... build with Fork + Triangles + Box ... )
    # diag.save_mmd("fixed_point.mmd")

    # 4. All four paper figures via dedicated renderers (guaranteed nice output)
    print(renderer.render_basic_monoidal("f", "g"))
    print(renderer.render_evaluator_law("p"))
    print(renderer.render_fixed_point_construction("succ"))
    print(renderer.render_data_service_comonoid())

    # 5. Roundtrip + validation + save
    d = StringDiagram(fork(Object("Ξ")), title="copy_demo")
    assert d.validate()
    d.save_mmd("/tmp/copy.mmd")

See also:
- diagrams/examples.py for more runnable snippets (agent steps, resources).
- The four static .mmd for visual reference targets.
- MonoidalComputer.build_fixed_point for executable counterpart.
"""

from __future__ import annotations

# Re-exports for ergonomic one-line imports
from .diagram import (
    Box,
    DiagramElement,
    Fork,
    Sequential,
    Stem,
    StringDiagram,
    Tensor,
    Triangle,
    Wire,
    box,
    fork,
    from_morphism,
    id_wire,
    seq,
    stem,
    tensor,
    triangle,
    wire,
)
from .mermaid_renderer import MermaidRenderer
from .safety import (
    SecurityFinding,
    SecurityReport,
    analyze_safety_geometry,
    generate_security_report,
)

__all__ = [
    # Core classes
    "StringDiagram",
    "Wire",
    "Box",
    "Triangle",
    "Fork",
    "Stem",
    "Sequential",
    "Tensor",
    "DiagramElement",
    "MermaidRenderer",
    # Builder helpers (preferred for most users)
    "wire",
    "box",
    "triangle",
    "fork",
    "stem",
    "seq",
    "tensor",
    "from_morphism",
    "id_wire",
    # Security analysis (structured reporting for reviews)
    "SecurityFinding",
    "SecurityReport",
    "analyze_safety_geometry",
    "generate_security_report",
]

# Version local to diagrams layer (package version is authoritative)
__diagrams_version__ = "0.1.0"
