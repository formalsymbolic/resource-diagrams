"""
resources.py — Explicit modeling of resources as first-class citizens in diagrams.

Resources (tokens, compute steps, information channels) are not implicit
side effects; they appear as wires, grades, or annotations. This makes
depletion, leakage, and accounting *structural* properties visible in
the string diagram.

Grounded in VISION.md ("resources as first-class") and the graded
monoidal computer ideas from Paper II, adapted for AI safety use cases:
token budgets in LLM calls, information flow for leakage analysis,
one-way (non-invertible) transforms for "hardness" of recovering
secrets or inverting attacks.

All items here compose with core.Object / core.Morphism and produce
or augment Diagram instances (see reasoning.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

from ..core import Object, Morphism
from ..data_services import DataService

# Diagram imported locally inside functions to avoid circular import with reasoning.py
# (reasoning defines Diagram; resources and agents use it for builders).


@dataclass(frozen=True)
class TokenBudget:
    """A token budget modeled as a graded resource object/wire.

    In a full graded monoidal computer this would carry a numeric grade
    (Paper II normal complexity). Here we use it for visualization and
    accounting in diagrams: each consuming step has an explicit Δ on
    the budget wire.

    Example safety use:
        A copied policy (Δ) can be applied in a context that also
        consumes tokens; the diagram shows whether budget exhaustion
        happens before or after a dangerous copied sub-policy executes.
    """

    name: str = "TokenBudget"
    limit: int = 4096
    used: int = 0

    def remaining(self) -> int:
        return max(0, self.limit - self.used)

    def consume(self, amount: int) -> "TokenBudget":
        """Return a new budget with consumption recorded (modeling only)."""
        return TokenBudget(self.name, self.limit, min(self.limit, self.used + amount))

    def to_object(self) -> Object:
        return Object(f"{self.name}[{self.remaining()}/{self.limit}]")

    def __repr__(self) -> str:
        return f"TokenBudget({self.name}, {self.used}/{self.limit})"


@dataclass(frozen=True)
class ComputeStep:
    """A discrete compute step (e.g. one forward pass, one tool invocation).

    Used to annotate Morphisms with resource cost. Can be tensored
    (visualized) alongside data wires.

    The produced Morphism uses a dummy impl stub (modeling/visualization only).
    """

    name: str
    cost_units: int = 1
    description: str = ""

    def to_morphism(self, src: Object, tgt: Object) -> Morphism:
        """Wrap as a core Morphism with *dummy* impl for modeling only.

        The _impl is a stub that records the named step + cost for traces,
        diagrams, and composition with evaluators. It has no real execution
        semantics (purely for visualization and the numeric monoidal model).
        """

        def _impl(x: Any) -> Any:
            # Pure modeling stub only (no actual compute; see docstring).
            return {"input": x, "compute_step": self.name, "cost": self.cost_units}

        return Morphism(
            name=self.name,
            src=src,
            tgt=tgt,
            impl=_impl,
            program_code=f"compute_step:{self.name}:{self.cost_units}",
        )


@dataclass
class InformationChannel:
    """Information channel with explicit copy (Δ) / delete (⊤) semantics.

    This is the key modeling tool for leakage and exfiltration analysis.

    - copyable=True  → DataService.copy valid (Δ fork in diagrams).
      Non-basic values (dicts etc.) use best-effort deepcopy when possible
      (central policy in DataService reduces prior alias risk for
      MemoryState/InformationChannel contents).
    - copyable=False → one-way or "delete after use". In diagrams: stem
      (⊤) or linear wire with no fork. Better for sensitive observations.

    The resulting annotations in diagrams surface exactly the properties
    that string diagrams from the papers make diagrammatically obvious
    for programs-as-data.
    """

    name: str
    copyable: bool = True
    description: str = ""

    def apply_copy(self, value: Any) -> Tuple[Any, Any]:
        """Δ operation (if allowed). Raises if not copyable.

        Delegates to DataService.copy (which does best-effort deepcopy for non-basic data)
        deepcopy for non-basic values like dicts to reduce aliasing risk,
        or warns+aliases on failure). Centralizes copy policy (no dup logic).
        """
        if not self.copyable:
            raise ValueError(f"Channel {self.name} is not copyable (one-way/delete-only)")
        obj = Object(self.name)
        return DataService.copy(value, obj)

    def apply_delete(self, value: Any) -> None:
        """⊤ operation — always allowed; discards the value."""
        obj = Object(self.name)
        DataService.delete(value, obj)

    def to_diagram_note(self) -> str:
        if self.copyable:
            return (
                f"Channel {self.name}: Δ (copyable) — "
                "value can be duplicated into multiple wires/contexts. "
                "Potential leakage/exfiltration surface if this channel "
                "carries policy, tool defs, or private observations."
            )
        return (
            f"Channel {self.name}: ⊤ (delete / one-way) — "
            "value flows linearly and is discarded after use. "
            "Reduces persistence of sensitive data in traces."
        )

    def __repr__(self) -> str:
        sem = "Δ-copyable" if self.copyable else "one-way/⊤"
        return f"InformationChannel({self.name}, {sem})"


@dataclass(frozen=True)
class OneWayTransform:
    """A non-invertible (one-way / hard-to-invert) morphism.

    Models transformations where recovering the preimage is difficult
    (the original motivation in the papers for measuring "hardness of
    deriving an attack program").

    In the diagram this is a box with no corresponding inverse program
    triangle. Useful for:
    - Tool response sanitization (hard to recover original secrets)
    - Output filters / safety classifiers (hard to invert)
    - Obfuscated policy fragments

    The `hardness` field is a modeling annotation (not a formal proof).

    Note: to_morphism produces a Morphism with dummy _impl (modeling stub only).
    """

    name: str
    src: Object
    tgt: Object
    hardness: str = "high (non-invertible by construction)"
    program_code: Optional[str] = None  # deliberately None or one-way only

    def to_morphism(self) -> Morphism:
        def _impl(x: Any) -> Any:
            # Dummy modeling stub: irreversible by construction in the model.
            # Records the transform for diagram/hardness annotation only.
            return {"transformed": x, "via": self.name, "invertible": False}

        return Morphism(
            name=self.name,
            src=self.src,
            tgt=self.tgt,
            impl=_impl,
            program_code=self.program_code,  # None or "oneway:..." signals non-invertible
        )


def model_token_accounting(
    steps: List[Tuple[str, int]],
    total_budget: int = 4096,
    title: Optional[str] = None,
) -> Diagram:
    """Worked example: produce a resource-annotated diagram for a token trace.

    steps: list of (step_name, tokens_consumed)
    Renders a main data flow with a parallel TokenBudget wire that is
    consumed at each step. Cumulative usage is explicit.

    Safety property surfaced: budget exhaustion points become visible
    structural features. A high-cost tool call late in a trace may
    occur after policy has already been copied (Δ) many times.

    Returns a Diagram (Mermaid + underlying Morphism steps for composition).
    """
    if title is None:
        title = f"Token Accounting Trace (budget={total_budget})"

    from .reasoning import Diagram  # local import avoids circularity

    d = Diagram(title=title)
    d.add_note(
        "Resource wire (TokenBudget) runs in parallel. "
        "Each box consumes along the resource wire (Δ on budget). "
        "This makes total usage and depletion path first-class."
    )

    budget = TokenBudget(limit=total_budget)
    prev_budget_obj = budget.to_object()

    # Start wire
    d.add_wire("UserContext", "initial context + copied policy (Δ)")

    cumulative = 0
    for i, (step_name, cost) in enumerate(steps):
        cumulative += cost
        new_budget = budget.consume(cost)
        new_budget_obj = new_budget.to_object()

        # Main data step
        step_morph = Morphism(
            name=step_name,
            src=Object("Context"),
            tgt=Object("Context'"),
            impl=lambda x, s=step_name, c=cost: {"step": s, "cost": c, "ctx": x},
            program_code=f"step:{step_name}",
        )
        d.add_morphism_step(step_morph)

        # Resource consumption annotation
        d.add_resource_consumption(
            resource_wire="TokenBudget",
            from_obj=prev_budget_obj,
            to_obj=new_budget_obj,
            amount=cost,
            step_name=step_name,
        )
        d.add_note(
            f"After {step_name}: cumulative={cumulative}, remaining={new_budget.remaining()}"
        )

        prev_budget_obj = new_budget_obj
        budget = new_budget

    d.add_note(
        "Safety insight: If any step above used a copied (Δ) policy or tool "
        "definition, the diagram shows the exact point where that duplicated "
        "data could have triggered high token spend (or a harmful action "
        "before budget exhaustion)."
    )
    # Use centralized constant + label for the safety interpretation.
    from .reasoning import TOKEN_SAFETY_INTERPRETATION

    d.safety_explanation = (
        "Illustrative interpretation of the shown geometry (budget wire + policy Δ annotations): "
        + TOKEN_SAFETY_INTERPRETATION
    )
    return d
