"""
Core types for Resource Diagrams.

Faithful implementation of the basic structures from the Monoidal Computer papers
(Pavlovic et al.), adapted for modeling AI systems and their resource properties.

References:
- Paper I (arXiv:1208.5205): Object/Morphism, monoidal structure (Fig 3 p.5),
  elements as triangles (p.6), composition and tensor.
- Diagrams/01_basic_string_diagrams.mmd for visual rules.
- Strict monoidal (no implicit associators; tensor names normalized flat
  for associativity transparency in names/equality).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class Object:
    """A data type / object in the monoidal category.

    In the context of AI systems, these represent types of data, states,
    resources, or information channels.

    Supports tensor (parallel composition of wires) and unit laws (I elided).
    Canonical objects defined below per Paper I §2–3.

    Tensor product is strict monoidal (associators elided per paper):
    .tensor produces flattened names so (A ⊗ B) ⊗ C == A ⊗ (B ⊗ C)
    by construction (associativity and naming normalization).
    """
    name: str

    def __repr__(self) -> str:
        return self.name

    def tensor(self, other: Object) -> Object:
        """A ⊗ B : monoidal product.

        Corresponds to parallel (horizontal) composition in string diagrams.
        Unitors: I ⊗ A ≅ A (wires can be elided when unit).

        Names are *flattened* (no nesting parentheses) so that different
        parenthesizations of the same sequence produce equal Objects with
        identical .name (e.g. (A @ B) @ C  and  A @ (B @ C) both yield
        Object("A ⊗ B ⊗ C")). This makes tensor names consistent with the
        paper's treatment of ⊗ as associative in the strict monoidal
        category (coherence elided; brackets dropped in diagrams).
        Manual construction of names with nested parens will differ.
        """
        if self.name == "I":
            return other
        if other.name == "I":
            return self
        # Flat form ensures associativity transparency for name and equality
        return Object(f"{self.name} ⊗ {other.name}")

    def __matmul__(self, other: Object) -> Object:
        """Convenience operator A @ B for tensor product."""
        return self.tensor(other)

    @property
    def is_unit(self) -> bool:
        """True for the monoidal unit I (terminal for data services)."""
        return self.name == "I"


# Canonical objects (Paper I, used throughout diagrams and constructions)
XI = Object("Ξ")  # universal type: programs live here as data + all values
N = Object("N")   # natural numbers
B = Object("B")   # booleans / truth values
I = Object("I")   # monoidal unit (target of delete ⊤)


@dataclass(frozen=True)
class Morphism:
    """A computation or process (morphism) in the category.

    Represents transformations, agent steps, tool calls, reasoning steps, etc.
    When `program_code` is present, the morphism can be treated as data
    (supporting copying, deletion, etc. via DataService).

    Strict frozen dataclass: immutable after construction (sensible for
    categorical structures; callables are allowed in frozen fields).

    Adds:
    - Composition ( ; ) via >> operator or direct call.
    - Tensor (⊗) via @ or .tensor
    - Factories: pure (extensional), program (intensional with code).
    """
    name: str
    src: Object
    tgt: Object
    # Executable behavior (for simulation / evaluation)
    impl: Callable[[Any], Any] = field(repr=False)
    # Optional intensional representation (the "program" as data)
    program_code: Optional[str] = None
    # Note: preserved/combined on ; and now also on ⊗; always
    # None for pure() factory. Enables DataService on tensor products.

    def __repr__(self) -> str:
        prog = f" ⌈{self.program_code}⌉" if self.program_code else ""
        return f"{self.name}{prog} : {self.src} → {self.tgt}"

    def to_diagram(self) -> "StringDiagram":
        """Return a StringDiagram consisting of this morphism rendered as a Box.

        Enables seamless integration: morph.to_diagram().to_mermaid() etc.
        The diagrams submodule must be importable (installed package).
        """
        # Lazy import to prevent circular dependency (diagrams depends on core)
        from .diagrams import from_morphism

        return from_morphism(self)

    def __rshift__(self, other: Morphism) -> Morphism:
        """Sequential composition self ; other (other after self).

        Matches vertical stacking in string diagrams (Paper I Fig 3).
        Raises on type mismatch.
        """
        if self.tgt != other.src:
            raise TypeError(
                f"Cannot compose {self} >> {other}: tgt/src mismatch "
                f"({self.tgt} != {other.src})"
            )

        def composed_impl(x: Any) -> Any:
            return other.impl(self.impl(x))

        new_prog: Optional[str] = None
        if self.program_code is not None and other.program_code is not None:
            new_prog = f"({self.program_code};{other.program_code})"

        return Morphism(
            f"({self.name};{other.name})",
            self.src,
            other.tgt,
            impl=composed_impl,
            program_code=new_prog,
        )

    def tensor(self, other: Morphism) -> Morphism:
        """Parallel composition / tensor product self ⊗ other.

        Matches horizontal juxtaposition in string diagrams.
        Expects 2-tuple input for (left, right) values in demo impl.

        program_code: if *both* have codes, synthesize "({c1} ⊗ {c2})" (symmetric
        to how >> combines with ; ). Otherwise None (extensional tensor).
        This makes tensor of intensional program-morphisms first-class data
        for DataService.copy (consistency improvement; was always discarding in some paths).
        """
        def tensor_impl(val: Any) -> Any:
            if isinstance(val, (tuple, list)) and len(val) == 2:
                v1, v2 = val
                return (self.impl(v1), other.impl(v2))
            # Demo fallback (not fully general; real use should supply pairs)
            return (self.impl(val), other.impl(val))

        new_src = self.src.tensor(other.src)
        new_tgt = self.tgt.tensor(other.tgt)

        new_prog: Optional[str] = None
        if self.program_code is not None and other.program_code is not None:
            new_prog = f"({self.program_code} ⊗ {other.program_code})"

        return Morphism(
            f"({self.name} ⊗ {other.name})",
            new_src,
            new_tgt,
            impl=tensor_impl,
            program_code=new_prog,
        )

    def __matmul__(self, other: Morphism) -> Morphism:
        """Syntactic sugar: m1 @ m2 for m1.tensor(m2)."""
        return self.tensor(other)

    def __call__(self, value: Any) -> Any:
        """Convenience: invoke the morphism as a function."""
        return self.impl(value)

    @classmethod
    def pure(
        cls, name: str, src: Object, tgt: Object, fn: Callable[[Any], Any]
    ) -> Morphism:
        """Factory for pure (extensional) functions without program_code.

        Use when only the input/output behavior matters, not the code.
        """
        return cls(name, src, tgt, impl=fn, program_code=None)

    @classmethod
    def program(
        cls,
        name: str,
        src: Object,
        tgt: Object,
        program_code: str,
        impl: Callable[[Any], Any],
    ) -> Morphism:
        """Factory for intensional programs with explicit program_code.

        The code makes the morphism first-class data for DataService.copy etc.
        (δ ∘ ⌈f⌉ = ⌈f⌉ ⊗ ⌈f⌉ for basic data programs.)
        """
        return cls(name, src, tgt, impl=impl, program_code=program_code)
