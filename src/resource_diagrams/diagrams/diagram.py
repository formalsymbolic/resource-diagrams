"""
Diagram element classes for programmatic construction of string diagrams.

These mirror the categorical structure (objects as wires, morphisms as boxes,
programs-as-data as triangles, data services as forks/stems) from the
Monoidal Computer papers. Composition via Sequential (;) and Tensor (⊗).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional, Union

from ..core import Morphism, Object

if TYPE_CHECKING:
    # Avoid runtime cycle (models will use these); core already imported
    pass


# -----------------------------------------------------------------------------
# Primitive diagram elements (wires, boxes, triangles, data service ops)
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Wire:
    """A wire labeled by an Object (the type flowing along the string)."""
    obj: Object
    label: Optional[str] = None

    def __post_init__(self) -> None:
        if self.label is None:
            # mutate frozen via object.__setattr__ is ok for init
            object.__setattr__(self, "label", str(self.obj))

    def __repr__(self) -> str:
        return f"Wire({self.label})"


@dataclass(frozen=True)
class Box:
    """A rectangular box representing a general morphism / process / agent step.

    Can wrap a core Morphism or be constructed with explicit label for
    pure diagrammatic use (e.g. evaluator u boxes, custom agent steps).
    """
    label: str
    src: Optional[Object] = None
    tgt: Optional[Object] = None
    morph: Optional[Morphism] = None
    program_code: Optional[str] = None  # for special labeling inside

    def __post_init__(self) -> None:
        if self.morph is not None:
            object.__setattr__(self, "label", self.morph.name)
            object.__setattr__(self, "src", self.morph.src)
            object.__setattr__(self, "tgt", self.morph.tgt)
            if self.morph.program_code and not self.program_code:
                object.__setattr__(self, "program_code", self.morph.program_code)

    def __repr__(self) -> str:
        return f"Box({self.label} : {self.src} → {self.tgt})"


@dataclass(frozen=True)
class Triangle:
    """A triangle (▼ p) representing a program / value / element as data.

    Typically p : I → X where X is usually Ξ (universal type).
    The program label appears inside the triangle in renderings.
    """
    program: str
    tgt: Object
    # Optional link back to a Morphism that this encodes (for roundtrips)
    encoded_morph: Optional[Morphism] = None

    def __repr__(self) -> str:
        return f"Triangle(▼ {self.program} → {self.tgt})"


@dataclass(frozen=True)
class Fork:
    """The copy operation Δ : A → A ⊗ A (comonoid fork, black dot in papers)."""
    obj: Object

    def __repr__(self) -> str:
        return f"Fork(Δ : {self.obj} → {self.obj} ⊗ {self.obj})"


@dataclass(frozen=True)
class Stem:
    """The delete operation ⊤ : A → I (comonoid stem)."""
    obj: Object

    def __repr__(self) -> str:
        return f"Stem(⊤ : {self.obj} → I)"


# -----------------------------------------------------------------------------
# Composition combinators (mirror monoidal category structure)
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Sequential:
    """Sequential composition ( ; ) : f ; g : A → C"""
    first: DiagramElement
    second: DiagramElement

    def __repr__(self) -> str:
        return f"Sequential({self.first} ; {self.second})"


@dataclass(frozen=True)
class Tensor:
    """Parallel / tensor composition ( ⊗ ) : f ⊗ g : A⊗L → B⊗M"""
    left: DiagramElement
    right: DiagramElement

    def __repr__(self) -> str:
        return f"Tensor({self.left} ⊗ {self.right})"


# Type alias for the recursive element tree
DiagramElement = Union[
    Wire, Box, Triangle, Fork, Stem, Sequential, Tensor
]


@dataclass(frozen=True)
class StringDiagram:
    """A complete string diagram.

    Rooted tree of elements. Supports validation of basic arity (src/tgt
    matching on Sequential), Mermaid export, text approx, and save.

    For AI safety modeling idioms (models/ layer), the following optional
    fields are supported (populated by high-level builders; do not affect
    core categorical structure or paper repro paths):
    - safety_explanation: human-readable interpretation of the safety
      properties made visible by the wiring (e.g. Δ policy copies vs
      one-way flows). "Illustrative interpretation of geometry" per
      project guidelines.
    - morphism_steps: the underlying executable trace (list of core.Morphism)
      for composition with evaluators etc. Preserves program_code etc.
    These make models builders return (or wrap) real StringDiagram while
    keeping ergonomic .safety_explanation and .steps access.
    """
    root: DiagramElement
    title: str = "string_diagram"
    # Optional metadata (e.g. paper figure reference)
    metadata: dict[str, Any] = field(default_factory=dict)
    # Models / safety annotation extensions (defaults preserve all prior usage)
    safety_explanation: Optional[str] = None
    morphism_steps: List[Morphism] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Basic validation on construction
        self._validate_arity()

    def _validate_arity(self) -> None:
        """Lightweight src/tgt arity check for Sequential (best-effort, minimal)."""
        # Only checks obvious Sequential cases; full inference left for future
        if isinstance(self.root, Sequential):
            # Heuristic: if both sides expose tgt/src via attrs, check rough match
            first = self.root.first
            second = self.root.second
            first_tgt = getattr(first, "tgt", None) or getattr(first, "obj", None)
            second_src = getattr(second, "src", None) or getattr(second, "obj", None)
            if first_tgt is not None and second_src is not None:
                if str(first_tgt) != str(second_src):
                    # Non-fatal for diagrams; just note in metadata
                    # frozen dataclass: use object setattr
                    object.__setattr__(
                        self,
                        "metadata",
                        {**self.metadata, "arity_warning": f"Possible mismatch: {first_tgt} -> {second_src}"},
                    )

    def validate(self) -> bool:
        """Return True if basic structural invariants appear satisfied."""
        return "arity_warning" not in self.metadata

    def to_mermaid(self, direction: str = "TD", **kwargs: Any) -> str:
        """Emit high-quality Mermaid flowchart reproducing or generalizing paper diagrams."""
        from .mermaid_renderer import MermaidRenderer

        renderer = MermaidRenderer()
        return renderer.render(self, direction=direction, **kwargs)

    def to_text(self) -> str:
        """ASCII/text approximation (inspired by prototype)."""
        return self._text_render(self.root, indent=0)

    def _text_render(self, elem: DiagramElement, indent: int = 0) -> str:
        pad = "  " * indent
        if isinstance(elem, Wire):
            return f"{pad}──[{elem.label}]──"
        if isinstance(elem, Box):
            prog = f" ⌈{elem.program_code}⌉" if elem.program_code else ""
            return f"{pad}[{elem.label}{prog}]"
        if isinstance(elem, Triangle):
            return f"{pad}▼ {elem.program}"
        if isinstance(elem, Fork):
            return f"{pad}Δ({elem.obj})"
        if isinstance(elem, Stem):
            return f"{pad}⊤({elem.obj})"
        if isinstance(elem, Sequential):
            return (
                f"{pad}( {self._text_render(elem.first, indent+1)}\n"
                f"{pad}  ; {self._text_render(elem.second, indent+1)} )"
            )
        if isinstance(elem, Tensor):
            return (
                f"{pad}( {self._text_render(elem.left, indent+1)}\n"
                f"{pad}  ⊗ {self._text_render(elem.right, indent+1)} )"
            )
        return f"{pad}{elem!r}"

    def save_mmd(self, path: str | Path, direction: str = "TD") -> None:
        """Save .mmd file (Mermaid source) for pasting into GitHub / viewers."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        content = self.to_mermaid(direction=direction)
        p.write_text(content, encoding="utf-8")

    def __repr__(self) -> str:
        extra = ""
        if self.safety_explanation:
            extra += ", has_safety_explanation"
        if self.morphism_steps:
            extra += f", {len(self.morphism_steps)} steps"
        return f"StringDiagram({self.title}, root={self.root}{extra})"


# -----------------------------------------------------------------------------
# Ergonomic builder helpers (standalone, work with or without core objects)
# -----------------------------------------------------------------------------

def wire(obj: Object, label: Optional[str] = None) -> Wire:
    """Create a labeled wire."""
    return Wire(obj, label)


def box(
    label: str,
    src: Optional[Object] = None,
    tgt: Optional[Object] = None,
    morph: Optional[Morphism] = None,
    program_code: Optional[str] = None,
) -> Box:
    """Create a box (morphism). Prefer passing a core Morphism when available."""
    if morph is not None:
        return Box(label="", morph=morph)  # label/src/tgt normalized in post_init
    return Box(label=label, src=src, tgt=tgt, program_code=program_code)


def triangle(program: str, tgt: Object, encoded_morph: Optional[Morphism] = None) -> Triangle:
    """Create a program triangle ▼ p."""
    return Triangle(program=program, tgt=tgt, encoded_morph=encoded_morph)


def fork(obj: Object) -> Fork:
    """Create a Δ copy fork."""
    return Fork(obj)


def stem(obj: Object) -> Stem:
    """Create a ⊤ delete stem."""
    return Stem(obj)


def seq(first: DiagramElement, second: DiagramElement) -> Sequential:
    """Sequential composition (f ; g)."""
    return Sequential(first, second)


def tensor(left: DiagramElement, right: DiagramElement) -> Tensor:
    """Tensor / parallel composition (f ⊗ g)."""
    return Tensor(left, right)


def from_morphism(m: Morphism) -> StringDiagram:
    """Convenience: turn a core Morphism into a single-box diagram."""
    return StringDiagram(Box("", morph=m), title=f"diagram_for_{m.name}")


def id_wire(obj: Object) -> StringDiagram:
    """Unit / identity wire (elidable in string diagrams)."""
    return StringDiagram(Wire(obj), title="identity_wire")
