"""
Universal and Partial Evaluators (Monoidal Computer, Paper I Def 4.1).

This module provides an *executable symbolic model* of ideas from
Definition 4.1 from Paper I (arXiv:1208.5205, p.17) together with the data services and
the fixed-point construction (Paper I §6, p.25-26, in the style of the diagrams in
diagrams/03_fixed_point_construction.mmd and 02_universal_evaluator_law.mmd).

- Universal evaluator u : Ξ ⊗ L → M    (the box with program triangle below)
- Partial evaluator s (specializer, approximation of categorical s-m-n / currying)
- Φ self-applicator built *purely* from DataService.copy (Δ) + apply (u)
- build_fixed_point provides a demonstration of the key mechanism behind
  the paper's graphical argument that every computation has a fixed point (using only program copying).

Construction traces are kept for reproducibility and diagram generation by
other agents.

In the AI context: programs = prompts, policies, tool specs, reasoning
procedures etc. as first-class copyable data.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .core import XI
from .data_services import DataService


class MonoidalComputer:
    """Executable symbolic model of a (numeric) Monoidal Computer per ideas in Paper I Def 4.1.

    Provides:
    - Registry of programs (intensional data, keyed by code strings on Ξ)
    - apply(...) : universal evaluator u
    - specialize(...) : partial evaluator s (demo approximation)
    - build_fixed_point(...) : demonstration of the fixed-point construction idea (Φ ; p in paper notation)
    - Clean registration API
    - Construction traces for the diagrammatic steps

    Satisfies (in this model):
    - The evaluator law (11): {p} ≔ u ∘ (p ⊗ id)
    - Basic fixed point equation via pure copy + u (no Gödel hacks; see caveats in build_fixed_point)

    All builtins chosen to be total or explicitly partiality-modeling,
    matching paper examples (succ for non-totality illustration).
    """

    def __init__(self) -> None:
        self._programs: dict[str, Callable[[Any], Any]] = {}
        self.construction_traces: list[str] = []
        self._register_core_programs()

    def _register_core_programs(self) -> None:
        """Register the minimal set of builtins used in the papers + demos.

        More can be added via the public register_program API.
        """
        # Identity on Ξ (baseline for many constructions)
        self.register_program("id", lambda x: x)

        # Successor — classic example in Paper I for a function with no
        # fixed point in N (leads to the "bottom" / partial element via Y).
        self.register_program("succ", lambda n: n + 1 if isinstance(n, int) else n)

        # iszero — simple control / branching example
        self.register_program("iszero", lambda n: (n == 0) if isinstance(n, int) else False)

        # Constant-0 (useful for other fixed-point examples)
        self.register_program("const0", lambda x: 0)

        # The self-application transformer Φ (Lemma 6.2).
        # Its implementation is built purely from DataService.copy + apply.
        self._programs["phi"] = self._phi_implementation

    def register_program(self, code: str, impl: Callable[[Any], Any]) -> None:
        """Clean public registration API for new programs (as data on Ξ).

        Registered programs automatically participate in copy (via is_basic_data),
        apply, specialize, and fixed-point constructions.
        """
        self._programs[code] = impl

    def _phi_implementation(self, p: Any) -> Any:
        """Φ : the self-application program transformer.

        {Φ}(p) = {p}(p)

        Built *purely* from DataService.copy (the Δ fork) + self.apply (u).
        This is the heart of the diagrammatic argument on Paper I p.26:
        because p (as basic data) satisfies δ ∘ p = p ⊗ p, we can duplicate
        the program triangle and wire one copy to the "program" input of u
        and one copy to the "data" input of u.

        See diagrams/03_fixed_point_construction.mmd .
        """
        if not isinstance(p, str):
            return None
        p1, p2 = DataService.copy(p, XI)
        return self.apply(p1, p2)

    # -------------------------------------------------------------------------
    # Universal Evaluator u (Def 4.1)
    # -------------------------------------------------------------------------
    def apply(self, program: str, input_value: Any) -> Any:
        """u(program, input) — the universal evaluator.

        Diagrammatic reading:
            input
              |
              v
          [ program triangle (▼ p, basic data) ]
              |
             [ u box ]
              |
              v
            result

        Corresponds to equation (11) in Paper I p.17:
            f = {p}   where  {p} ≔ u ∘ (p ⊗ id_L)
        """
        if program not in self._programs:
            return None  # partial / non-halting / unknown program
        impl = self._programs[program]
        try:
            return impl(input_value)
        except Exception:
            return None

    # -------------------------------------------------------------------------
    # Partial Evaluator s (Def 4.1, s-m-n)
    # -------------------------------------------------------------------------
    def specialize(self, program: str, fixed_input: Any) -> str:
        """s(program, fixed_input) → new_program_code

        The partial evaluator / specializer.

        The returned program, when applied to remaining args, behaves as
        the original with the first argument fixed to fixed_input.

        This is a demo implementation approximating the categorical s-m-n / currying
        in the monoidal setting (see implementation note).

        Implementation note: manufactures a fresh code and closure.
        A richer model would manipulate ASTs of programs.
        """
        new_code = f"spec({program},{fixed_input})"
        original = self._programs.get(program, lambda x: None)
        self._programs[new_code] = lambda remaining: original((fixed_input, remaining))
        self.construction_traces.append(f"specialize({program!r}, {fixed_input!r}) → {new_code!r}")
        return new_code

    # -------------------------------------------------------------------------
    # Fixed Point Construction (simple model inspired by Paper I)
    # -------------------------------------------------------------------------
    def build_fixed_point(self, p_code: str) -> tuple[str, Any]:
        """A simple demonstration inspired by the fixed-point construction in
        Paper I §6.

        This implementation works in an extended domain where non-integer
        values (including program name strings) are treated as fixed points
        for the successor example. It is useful for illustrating the
        diagrammatic idea but is a toy model, not a faithful or rigorous
        realization of the theorem.
        """
        self.construction_traces.append(
            f"build_fixed_point(⌈{p_code}⌉) — Paper I p.25-26 / diagrams/03_fixed_point_construction.mmd"
        )

        # Step 1: Φ(p) via pure copy + u  ===  {p}(p)
        e = self.apply("phi", p_code)
        self.construction_traces.append(f"  Φ(p) = {e!r}   (via DataService.copy + apply)")

        fp_meaning = e
        fp_code = f"fix({p_code})"

        # Register fp_code as a program that constantly yields the fixed-point
        # witness. This makes "apply the fp program to itself" well-defined
        # and equal to the meaning (for verification of the equation).
        self._programs[fp_code] = lambda _input: fp_meaning

        # Step 2 (law verification for trace)
        p_on_fp = self.apply(p_code, fp_meaning) if fp_meaning is not None else None
        law_holds = p_on_fp == fp_meaning
        self.construction_traces.append(
            f"  Registered {fp_code}. Law {{ {p_code} }}(fp_meaning) == fp_meaning ? "
            f"{law_holds} ({p_on_fp!r} == {fp_meaning!r})"
        )

        self.construction_traces.append(f"  Result: fp_code={fp_code}, fp_meaning={fp_meaning!r}")
        return fp_code, fp_meaning

    def get_construction_trace(self) -> str:
        """Return the accumulated construction trace as a single string."""
        return "\n".join(self.construction_traces)

    def clear_traces(self) -> None:
        """Reset traces (useful between independent constructions)."""
        self.construction_traces = []
