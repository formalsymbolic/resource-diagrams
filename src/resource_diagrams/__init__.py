"""
Resource Diagrams

A self-contained library for diagrammatic analysis of resources in AI systems,
based on the Monoidal Computer framework (Pavlovic et al.).

Core ideas:
- Programs and computations as first-class data
- String diagrams as a high-level reasoning tool
- Focus on resources, one-way transformations, and security-relevant properties

Primary use: AI safety, security analysis, and scalable oversight of agentic systems.

The diagrams submodule (string diagram DSL + MermaidRenderer) is the primary
interface for construction and rendering of the paper figures and AI models.
"""

__version__ = "0.1.0"

from .core import Object, Morphism, XI, N, B, I
from .data_services import DataService
from .evaluators import MonoidalComputer


def build_example_monoidal_computer() -> MonoidalComputer:
    """Return a fresh MonoidalComputer pre-populated with the standard
    builtins (id, succ, iszero, phi, ...) for demos and tests.

    This is the entry point for reproducing the Paper I constructions
    (fixed point of succ, evaluator law, etc.).
    """
    return MonoidalComputer()

# Diagrams layer (string diagram construction + Mermaid export for paper figures)
from . import diagrams

# Models layer (AI idioms: ReAct loops, token accounting, info-flow with Δ/⊤)
# See resource_diagrams.models for builders and safety-focused documentation.
from . import models

# Explicit re-export for convenience (structural safety analysis)
from .diagrams.safety import (
    SecurityFinding,
    SecurityReport,
    analyze_safety_geometry,
    generate_security_report,
)

# Note: for the flat names (StringDiagram, box, etc.) prefer
#   from resource_diagrams.diagrams import StringDiagram, ...
# or access via resource_diagrams.diagrams.StringDiagram
# Lazy re-export of common names to support "from resource_diagrams import StringDiagram"
_DIAGRAMS_EXPORTS = (
    "StringDiagram",
    "Wire",
    "Box",
    "Triangle",
    "Fork",
    "Stem",
    "Sequential",
    "Tensor",
    "MermaidRenderer",
    "wire",
    "box",
    "triangle",
    "fork",
    "stem",
    "analyze_safety_geometry",
    "generate_security_report",
    "SecurityReport",
    "SecurityFinding",
    "seq",
    "tensor",
    "from_morphism",
)


def __getattr__(name: str):
    if name in _DIAGRAMS_EXPORTS:
        from . import diagrams as _diagrams_mod

        if name in _diagrams_mod.__dict__:
            return _diagrams_mod.__dict__[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_DIAGRAMS_EXPORTS))


__all__ = [
    "Object",
    "Morphism",
    "XI",
    "N",
    "B",
    "I",
    "DataService",
    "MonoidalComputer",
    "build_example_monoidal_computer",
    "diagrams",
    "models",
    # diagrams names also reachable via top-level import (lazy)
    *_DIAGRAMS_EXPORTS,
]
