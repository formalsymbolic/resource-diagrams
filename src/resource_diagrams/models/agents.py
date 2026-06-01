"""
agents.py — Builders for agent scaffolds expressed as resource diagrams.

Focus: ToolCall (morphism carrying explicit resource cost), ReActLoop /
AgentStep (composite reason + tool + observe with trace), MemoryState
(object with explicit Δ for copying context into next step).

These constitute two of the primary modeling patterns developed in the models layer:
- ReAct-style loops as diagrams (see examples and notebooks for usage patterns)
- Making visible the copying of policy/tool definitions (programs as data)
  vs one-way flow of user queries and observations.

All output is modeling/visualization only. The Morphisms produced by
builders (ToolCall etc.) carry *dummy* impls that record structure for
diagrams/traces (no real execution). The returned Diagram contains
a `.steps` list of core.Morphism for further composition with evaluators
or the diagrams/ layer, plus Mermaid rendering and safety explanations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ..core import Object, Morphism
from ..data_services import DataService

# Local imports of Diagram inside functions (see resources.py for rationale)


@dataclass(frozen=True)
class ToolCall:
    """A tool invocation modeled as a Morphism with attached resource cost.

    The `program_code` (when present) makes the *tool definition itself*
    basic data that can be copied (Δ). This is central to the diagrammatic
    view: the description of what the tool does and how to call it is
    duplicable into the agent's context on every cycle.

    Safety relevance: copied tool definitions can be reflected back in
    outputs, logged, or used to construct follow-up attacks.

    Note: the Morphism.impl is a dummy stub for modeling/visualization only
    (records the call; see to_morphism source). No runtime tool dispatch.
    """

    name: str
    cost_tokens: int = 50
    description: str = ""

    def to_morphism(self, src: Object, tgt: Object) -> Morphism:
        def _impl(x: Any) -> Any:
            # Dummy modeling stub only: records tool name/cost for diagram
            # and trace purposes. No real tool execution or side effects.
            return {
                "tool": self.name,
                "args": x,
                "simulated_result": f"result_from_{self.name}",
                "cost": self.cost_tokens,
            }

        prog = f"tool_def:{self.name}:{self.description[:30]}"
        return Morphism(
            name=f"ToolCall[{self.name}]",
            src=src,
            tgt=tgt,
            impl=_impl,
            program_code=prog,  # makes it copyable basic data
        )


@dataclass(frozen=True)
class MemoryState:
    """Agent memory / context state.

    Explicitly supports Δ (copy) for forking context into reasoner,
    tool args, and next-cycle memory. This models the "scratchpad"
    or conversation history that accumulates copied policy fragments.

    Note: .copy() delegates to DataService.copy (may alias for non-basic
    content like dicts; see core data_services for details).
    """

    name: str = "Memory"
    content: Any = field(default_factory=dict, repr=False)

    def copy(self) -> tuple["MemoryState", "MemoryState"]:
        """Δ : duplicate the memory state (for diagrammatic context sharing)."""
        obj = Object(self.name)
        c1, c2 = DataService.copy(self.content, obj)
        return (
            MemoryState(self.name, c1),
            MemoryState(self.name, c2),
        )

    def to_object(self) -> Object:
        return Object(self.name)


@dataclass
class AgentStep:
    """A single step in an agent trace (reason, tool, observe, etc.).

    Carries the underlying Morphism plus resource annotations and
    whether policy/tool data was copied (Δ) into it.
    """

    morph: Morphism
    copied_policy: bool = False
    resource_notes: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        cp = " [Δ policy]" if self.copied_policy else ""
        res = f" resources={self.resource_notes}" if self.resource_notes else ""
        return f"AgentStep({self.morph}{cp}{res})"


@dataclass
class ReActCycle:
    """One full ReAct cycle: Reason → (optional) ToolCall(s) → Observe.

    The cycle itself is a composite that can be sequenced. The diagram
    form makes the Δ on the policy wire at the start of each cycle explicit.
    """

    cycle_id: int
    reason_step: AgentStep
    tool_steps: List[AgentStep]
    observe_step: AgentStep
    memory_before: MemoryState
    memory_after: MemoryState

    def to_morphisms(self) -> List[Morphism]:
        return (
            [self.reason_step.morph]
            + [t.morph for t in self.tool_steps]
            + [self.observe_step.morph]
        )


def build_simple_react_diagram(
    tools: List[str],
    cycles: int = 1,
    title: Optional[str] = None,
) -> "Diagram":
    """Worked example builder #1 (high value): ReAct-style loop as diagram.

    Constructs a trace with `cycles` iterations of:
        reason (using copied policy Δ + user context) →
        tool_call(s) (each with token cost, tool def also copied) →
        observe (one-way result wire, typically no Δ)

    The returned Diagram contains:
    - .steps : List[Morphism]  (the executable trace for core/evaluators)
    - .to_mermaid() : full graph
    - .safety_explanation : detailed text on the security property made visible

    This is the primary "why it matters for AI safety" artifact.

    Safety property made visible (verbatim from the docstring intent):
        "This diagram makes visible that the tool definition (program triangle)
        can be copied into the context (via Δ) while the user query flows
        only one way (no Δ on the query wire). The policy and tool specs
        therefore persist and can be reflected in every subsequent memory
        state and observation, whereas the original user query does not
        automatically duplicate into tool arguments or long-term memory.
        This asymmetry is exactly the surface used in many prompt-injection
        and policy-exfiltration attacks."

    The diagram also annotates token costs on a parallel resource wire
    (see model_token_accounting for deeper accounting).
    """
    if title is None:
        title = f"Simple ReAct Loop (tools={tools}, cycles={cycles})"

    from .reasoning import Diagram  # local to break potential cycles
    from ..diagrams import (
        StringDiagram,
        fork,
        stem,
        triangle,
        seq,
        tensor,
        wire,
        box,
    )
    from ..diagrams.diagram import DiagramElement

    d = Diagram(title=title)

    # Canonical objects
    query_obj = Object("UserQuery")
    policy_obj = Object("AgentPolicy+ToolDefs")  # the "program triangle" — basic data
    context_obj = Object("Context")
    obs_obj = Object("Observation")

    d.add_note(
        "PROGRAM TRIANGLE (▼): AgentPolicy+ToolDefs — basic data, "
        "supports Δ (copy) into every reasoner invocation and tool context. "
        "This is the source of persistence and potential exfiltration."
    )
    d.add_triangle("policy", "▼ AgentPolicy + tool definitions (copyable via Δ)")

    d.add_note(
        "QUERY WIRE: UserQuery enters once (no Δ fork). It is consumed "
        "one-way into the first reason step. No automatic duplication."
    )
    d.add_wire("query", "UserQuery (one-way, no Δ)")

    all_steps: List[Morphism] = []
    cumulative_tokens = 0

    for c in range(cycles):
        # Memory / context fork (Δ) at start of cycle — policy already in it
        mem = MemoryState(f"Memory_cycle{c}")
        m1, m2 = mem.copy()
        d.add_note(f"Cycle {c}: MemoryState Δ fork (context sharing)")

        # Reason step (uses copied policy + current context)
        reason_m = Morphism(
            name=f"Reason[{c}]",
            src=context_obj,
            tgt=context_obj,
            impl=lambda x, cyc=c: {"thought": f"thinking_{cyc}", "plan": "use tool", "ctx": x},
            program_code=f"reasoner_policy_copy_{c}",  # signals Δ was used
        )
        reason_step = AgentStep(
            morph=reason_m,
            copied_policy=True,
            resource_notes=["policy_Δ_applied"],
        )
        d.add_morphism_step(reason_m, copied_policy=True)
        all_steps.append(reason_m)

        # Tool calls (each tool def also copyable)
        tool_steps_this_cycle: List[AgentStep] = []
        for tool_name in tools:
            tc = ToolCall(tool_name, cost_tokens=80, description=f"Tool {tool_name}")
            tool_m = tc.to_morphism(context_obj, obs_obj)
            t_step = AgentStep(
                morph=tool_m,
                copied_policy=True,  # tool def copied into call site
                resource_notes=[f"tool_cost:{tc.cost_tokens}"],
            )
            d.add_morphism_step(tool_m, copied_policy=True, cost=tc.cost_tokens)
            tool_steps_this_cycle.append(t_step)
            all_steps.append(tool_m)
            cumulative_tokens += tc.cost_tokens

        # Observe step — result flows one way (model as non-Δ by default)
        obs_m = Morphism(
            name=f"Observe[{c}]",
            src=obs_obj,
            tgt=context_obj,
            impl=lambda x: {"observation": x, "integrated": True},
            program_code=None,  # observation typically not "program data"
        )
        obs_step = AgentStep(morph=obs_m, copied_policy=False, resource_notes=["one_way_obs"])
        d.add_morphism_step(obs_m, copied_policy=False)
        all_steps.append(obs_m)

        # Record the cycle
        cycle = ReActCycle(
            cycle_id=c,
            reason_step=reason_step,
            tool_steps=tool_steps_this_cycle,
            observe_step=obs_step,
            memory_before=mem,
            memory_after=MemoryState(f"Memory_after_{c}"),
        )
        d.add_note(
            f"Cycle {c} complete. Cumulative tool tokens so far: {cumulative_tokens}. "
            "Note the Δ on policy/tool wires vs linear query/obs flow."
        )

    # Note: no need to assign d.steps = all_steps (add_morphism_step calls
    # in the loop already populated .steps via the same morphs; removed
    # prior redundant assignment + ignore (frozen dataclass hygiene).
    # Use centralized constant for the safety interpretation text.
    # The text interprets annotations (copied_policy flags, program_code on
    # policy steps) that proxy for Δ forks vs one-way wires in the trace.
    from .reasoning import REACT_SAFETY_INTERPRETATION

    d.safety_explanation = (
        "Illustrative interpretation of the shown geometry (and trace annotations): "
        + REACT_SAFETY_INTERPRETATION
    )

    # --- Structural diagram construction (unification) ---
    # Build a real StringDiagram using the diagrams/ primitives (fork, stem, triangle,
    # box, seq, tensor, wire). This makes Δ policy forks and one-way (Stem) paths
    # first-class categorical structure rather than annotations only.
    # The resulting tree powers analyze_safety_geometry and to_string_diagram().
    # Layout uses a representative skeleton of the key geometry (policy entry fork
    # + per-step boxes + explicit Stem on observations) because full multi-cycle
    # 2D string layout is out of Phase 1 scope; the .morphism_steps and legacy
    # .to_mermaid() (via Diagram facade) provide the complete trace view.
    policy_tri = triangle("AgentPolicy+ToolDefs", policy_obj)
    query_w = wire(query_obj, "UserQuery (one-way)")

    # Entry: policy triangle tensor one-way query, then explicit Δ fork on policy path
    entry = tensor(policy_tri, query_w)
    struct_root: DiagramElement = seq(entry, fork(policy_obj))

    # Representative steps with explicit Stem (⊤ delete) after each Observe.
    # This is the diagrammatic signature of "guarding" a one-way channel.
    for step in all_steps:
        b = box(
            step.name,
            src=context_obj,
            tgt=obs_obj if "Observe" in step.name else context_obj,
            program_code=step.program_code,
        )
        struct_root = seq(struct_root, b)
        if "Observe" in step.name:
            # Explicit delete on the observation wire after integration.
            # Absence of a corresponding Fork on this path is the "one-way" marker.
            struct_root = seq(struct_root, stem(obs_obj))

    sd = StringDiagram(
        root=struct_root,
        title=title,
        safety_explanation=d.safety_explanation,
        morphism_steps=all_steps,
    )
    d.string_diagram = sd

    # Structural analyzer now always runs on a real tree (no fallback).
    from ..diagrams.safety import analyze_safety_geometry
    analysis = analyze_safety_geometry(sd)
    d.add_note(
        f"STRUCTURAL ANALYSIS: {analysis['policy_forks']} policy forks (Δ), "
        f"{analysis['one_way_paths']} one-way paths (Stem/Wire). "
        "Safety geometry is now derived from the categorical element tree."
    )

    return d


# -----------------------------------------------------------------------------
# Guarded vs Unguarded contrast pattern (highest-ROI applied extension)
# -----------------------------------------------------------------------------

@dataclass
class GuardedContrast:
    """Result of build_guarded_vs_unguarded_contrast.

    Both diagrams use identical policy/tool copying (Δ fork on program triangle)
    into the critical step. The sole structural difference is the presence of
    an explicit Stem (⊤ delete) on the sensitive one-way channel in the guarded
    version. This is the diagrammatic embodiment of "guarding after use".
    """
    unguarded: "Diagram"
    guarded: "Diagram"
    analysis_unguarded: Dict[str, Any]
    analysis_guarded: Dict[str, Any]
    explanation: str


def build_guarded_vs_unguarded_contrast(
    sensitive_label: str = "UserPrivateFact",
    tool_name: str = "search",
    title_prefix: str = "Sensitive Channel Handling",
) -> GuardedContrast:
    """One more applied pattern: explicit contrast of guarded vs unguarded
    one-way channels in an otherwise identical agent step.

    Unguarded: policy Δ forks into tool; sensitive input (one-way wire) also
    reaches the tool box with no subsequent delete. The secret has an open
    lifetime in the diagram geometry.

    Guarded: identical policy fork and tool box, but after the sensitive value
    is consumed an explicit Stem (⊤) deletes it. The wire does not continue;
    persistence surface is structurally closed.

    Both return full Diagram facades (with .string_diagram populated) plus
    the raw analyzer dicts so callers can see the metric delta (stems,
    has_explicit_guards) directly. This is immediately useful for design
    reviews and red-teaming of agent scaffolds that handle secrets/PII/tools.

    Self-contained; no external services.
    """
    from ..core import Object, Morphism
    from ..diagrams import (
        StringDiagram,
        box,
        fork,
        seq,
        stem,
        tensor,
        triangle,
        wire,
    )
    from ..diagrams.safety import analyze_safety_geometry
    from .reasoning import Diagram, REACT_SAFETY_INTERPRETATION

    policy_obj = Object("AgentPolicy")
    secret_obj = Object(sensitive_label)
    ctx_obj = Object("Context")

    # Common policy triangle (copyable program data)
    pol_tri = triangle("AgentPolicy+ToolDefs", policy_obj)

    # --- UNGUARDED ---
    # (policy ⊗ secret) ; fork(policy) ; tool_box   [secret wire has no stem]
    entry_u = tensor(pol_tri, wire(secret_obj, f"{sensitive_label} (one-way, unguarded)"))
    fork_u = fork(policy_obj)
    tool_box_u = box(
        f"Tool[{tool_name}]",
        src=ctx_obj,
        program_code=f"tool_def:{tool_name}",
    )
    root_u = seq(seq(entry_u, fork_u), tool_box_u)

    sd_u = StringDiagram(
        root=root_u,
        title=f"{title_prefix} — UNGUARDED",
        safety_explanation=(
            "Illustrative interpretation: The sensitive input reaches the tool "
            "without an explicit delete (no Stem on its wire). Combined with "
            "Δ on policy, this geometry leaves an open surface for the secret "
            "to be reflected, logged, or exfiltrated via the copied policy path."
        ),
        morphism_steps=[],
    )

    d_u = Diagram(title=sd_u.title)
    d_u.string_diagram = sd_u
    d_u.safety_explanation = sd_u.safety_explanation
    d_u.add_note("UNGUARDED pattern: one-way secret has no Stem after use.")

    # --- GUARDED ---
    # Same entry + fork + tool, then explicit stem on the secret path after consumption
    entry_g = tensor(pol_tri, wire(secret_obj, f"{sensitive_label} (one-way, will be stemmed)"))
    fork_g = fork(policy_obj)
    tool_box_g = box(
        f"Tool[{tool_name}]",
        src=ctx_obj,
        program_code=f"tool_def:{tool_name}",
    )
    root_g = seq(seq(entry_g, fork_g), tool_box_g)
    root_g = seq(root_g, stem(secret_obj))  # THE GUARD: explicit delete

    sd_g = StringDiagram(
        root=root_g,
        title=f"{title_prefix} — GUARDED (explicit Stem)",
        safety_explanation=(
            "Illustrative interpretation: After the sensitive value is used by "
            "the tool, an explicit Stem (⊤) deletes it. The one-way channel is "
            "now structurally terminated. Policy still forks (Δ) for legitimate "
            "reuse, but the secret does not persist alongside it. This is the "
            "diagrammatic act of guarding."
        ),
        morphism_steps=[],
    )

    d_g = Diagram(title=sd_g.title)
    d_g.string_diagram = sd_g
    d_g.safety_explanation = sd_g.safety_explanation
    d_g.add_note("GUARDED pattern: explicit Stem (⊤) terminates the sensitive wire.")

    # Analyses
    a_u = analyze_safety_geometry(sd_u)
    a_g = analyze_safety_geometry(sd_g)

    explanation = (
        "Guarded vs Unguarded contrast (core hook made quantitative):\n"
        f"  Unguarded: policy_forks={a_u['policy_forks']}, stems={a_u['stems']}, "
        f"has_explicit_guards={a_u['has_explicit_guards']}\n"
        f"  Guarded:   policy_forks={a_g['policy_forks']}, stems={a_g['stems']}, "
        f"has_explicit_guards={a_g['has_explicit_guards']}\n"
        "Inserting a Stem on the one-way sensitive path is the structural "
        "difference that closes the persistence surface while preserving "
        "necessary policy copying (Δ)."
    )

    return GuardedContrast(
        unguarded=d_u,
        guarded=d_g,
        analysis_unguarded=a_u,
        analysis_guarded=a_g,
        explanation=explanation,
    )
