"""
agents.py — Builders for agent scaffolds expressed as resource diagrams.

Focus: ToolCall (morphism carrying explicit resource cost), ReActLoop /
AgentStep (composite reason + tool + observe with trace), MemoryState
(object with explicit Δ for copying context into next step).

Core patterns (original):
- ReAct-style loops as diagrams
- Policy/tool copy (Δ) vs one-way user/obs flow

New non-trivial extensions (this module):
- Hierarchical/nested agents: inner agents modeled as first-class policy
  resources (triangles) that supervisor can Δ-copy or use linearly+stem.
- Explicit self-critique/reflexion: separate critic policy fork + one-way
  observation boundary from actor + per-critic resource accounting.
- Multi-agent coordination: private per-agent policies/channels vs shared
  Δ-copyable blackboard, explicit merge/consensus boxes, stems for boundaries.

These are implemented as clean builders producing full StringDiagram trees
(so analyze_safety_geometry and path-sensitive influence tracking apply
directly, with per-type fork classification for sub-policies, critic policies,
private channels, shared memory etc.).

All output is modeling/visualization only. The Morphisms produced by
builders (ToolCall etc.) carry *dummy* impls that record structure for
diagrams/traces (no real execution). The returned Diagram contains
a `.steps` list of core.Morphism for further composition with evaluators
or the diagrams/ layer, plus Mermaid rendering and safety explanations.
"""


from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core import Morphism, Object
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

    def copy(self) -> tuple[MemoryState, MemoryState]:
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
    resource_notes: list[str] = field(default_factory=list)

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
    tool_steps: list[AgentStep]
    observe_step: AgentStep
    memory_before: MemoryState
    memory_after: MemoryState

    def to_morphisms(self) -> list[Morphism]:
        return [self.reason_step.morph] + [t.morph for t in self.tool_steps] + [self.observe_step.morph]


def build_simple_react_diagram(
    tools: list[str],
    cycles: int = 1,
    title: str | None = None,
) -> Diagram:
    """Worked example builder #1 (high value): ReAct-style loop as diagram.

    Constructs a trace with `cycles` iterations of:
        reason (using copied policy Δ + user context) →
        tool_call(s) (each with token cost, tool def also copied) →
        observe (one-way result wire, typically no Δ)

    The returned Diagram contains:
    - .steps : List[Morphism]  (the executable trace for core/evaluators)
    - .to_mermaid() : full graph
    - .safety_explanation : detailed illustrative text on the structural pattern highlighted

    This is the primary artifact for exploring "why the diagrammatic view might matter for AI safety research".

    Illustrative pattern highlighted (verbatim from the docstring intent):
        "This diagram highlights that the tool definition (program triangle)
        can be copied into the context (via Δ) while the user query flows
        only one way (no Δ on the query wire). The policy and tool specs
        therefore persist and can be reflected in every subsequent memory
        state and observation, whereas the original user query does not
        automatically duplicate into tool arguments or long-term memory.
        This asymmetry corresponds to a structural pattern discussed in the
        context of prompt-injection and policy-exfiltration scenarios."

    The diagram also annotates token costs on a parallel resource wire
    (see model_token_accounting for deeper accounting).
    """
    if title is None:
        title = f"Simple ReAct Loop (tools={tools}, cycles={cycles})"

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
    from ..diagrams.diagram import DiagramElement
    from .reasoning import Diagram  # local to break potential cycles

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

    all_steps: list[Morphism] = []
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
        tool_steps_this_cycle: list[AgentStep] = []
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
        ReActCycle(
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
        "Illustrative interpretation of the shown geometry (and trace annotations): " + REACT_SAFETY_INTERPRETATION
    )  # (already labeled illustrative in the constant)

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

    unguarded: Diagram
    guarded: Diagram
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
    from ..core import Object
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
    from .reasoning import Diagram

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


# =============================================================================
# NEW MODELING PATTERNS (high-leverage, non-trivial extensions)
# Hierarchical/nested, explicit reflexion/critique with accounting, multi-agent
# coordination with boundaries. All produce StringDiagram (structural Δ/⊤
# geometry + analyzer) + ergonomic Diagram facade.
# =============================================================================


@dataclass
class HierarchicalAgentResult:
    """Container for the hierarchical builder (for advanced callers that want
    the raw analysis separate from the Diagram facade). Most users just use
    the .diagram which has .string_diagram, .to_mermaid(), .safety_explanation
    and notes containing analyzer output.
    """

    diagram: Diagram
    analysis: dict[str, Any]
    explanation: str


def build_hierarchical_agent_diagram(
    subagent_names: list[str] | None = None,
    supervisor_name: str = "SupervisorPolicy",
    title: str | None = None,
) -> Diagram:
    """Builder for Pattern 1: Hierarchical / nested agent structures.

    Inner agents are modeled as *resources*: each has its own program
    triangle (▼ SubAgentPolicy_XXX) that appears in the diagram alongside
    the supervisor's. These can be:
      - Δ-forked (copied) so the supervisor can "distribute" or reuse the
        sub-agent's full policy definition across multiple delegation sites
        (multiplies the sub-policy lifetime surface).
      - Used linearly: the sub-triangle influence flows into a delegate box
        without an explicit fork on that sub-obj, then stemmed after use.

    Structure (via primitives):
    - tensor( sup_triangle , tensor_of_sub_triangles )  -- subs as parallel resources
    - seq( ..., fork(sup) )  -- supervisor copies its own policy
    - decide box (sup)
    - per sub: [optional fork(sub_obj) for copyable case] ; delegate_box ; sub_run_box ; stem(obs)
    - final integrate

    Why non-trivial / high-signal:
    - Treats "agents" themselves as copyable data (like tools/policies), enabling
      modeling of "agent factories", "sub-agent spawning with code copy",
      "recursive scaffolds", or "policy exfiltration of sub-agents".
    - The SafetyAnalyzer's classify + live influence will see forks_by_type
      including 'policy' for subs (because "SubAgentPolicy" matches), plus
      separate reaches under policy_copy for sub-obs.
    - Explicit stems on sub-obs after inner execution bound the sub outputs.
    - Contrast to flat ReAct: here there are *nested* policy lifetimes visible
      in one diagram (sup forks + sub forks coexisting in the live set).

    The returned Diagram has full .string_diagram for analyzer and rendering.
    """
    if subagent_names is None:
        subagent_names = ["research_sub", "code_sub"]
    if title is None:
        title = f"Hierarchical/Nested Agent (sup={supervisor_name}, subs={subagent_names})"

    from ..core import Object
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
    from .reasoning import Diagram

    sup_obj = Object(supervisor_name)
    sub_objs = [Object(f"SubAgentPolicy_{n}") for n in subagent_names]
    ctx_obj = Object("SupervisorContext")
    obs_obj = Object("SubObservation")

    # Supervisor triangle (copyable policy)
    sup_tri = triangle(supervisor_name, sup_obj)

    # Sub-agent policies as explicit resource triangles (the key modeling move)
    sub_tris = [triangle(f"SubPolicy:{n}", so) for n, so in zip(subagent_names, sub_objs)]
    # Bundle as nested tensor (parallel availability of sub resources)
    subs_bundle: Any = sub_tris[0]
    for st in sub_tris[1:]:
        subs_bundle = tensor(subs_bundle, st)

    entry = tensor(sup_tri, subs_bundle)
    root: Any = seq(entry, fork(sup_obj))  # Δ on supervisor policy

    # Supervisor decision (uses copied sup policy via the fork influence)
    decide = box(
        "SupervisorDecide+Plan",
        src=ctx_obj,
        tgt=ctx_obj,
        program_code=f"supervisor:{supervisor_name}:decide",
    )
    root = seq(root, decide)

    # For each sub-agent: demonstrate copyable vs linear use of the *inner* policy resource
    for i, (name, so) in enumerate(zip(subagent_names, sub_objs)):
        if i == 0:
            # Copyable use of inner agent: explicit Δ fork on the sub-policy obj
            root = seq(root, fork(so))
            use_label = f"DelegateTo[{name}] [Δ copied subpolicy]"
        else:
            # Linear use of the sub-policy resource (no fork on this sub obj here)
            use_label = f"DelegateTo[{name}] [linear subpolicy use]"

        del_box = box(
            use_label,
            src=ctx_obj,
            tgt=obs_obj,
            program_code=f"delegate_sub:{name}",
        )
        root = seq(root, del_box)

        # Inner agent execution (the "nested" run; its policy was the triangle/fork above)
        sub_exec = box(
            f"InnerAgent[{name}].run",
            src=obs_obj,
            tgt=obs_obj,
            program_code=f"subpolicy:{name}:exec",  # signals sub's own (copied or linear) policy in use
        )
        root = seq(root, sub_exec)

        # Guard: stem the observation from the sub (one-way from inner; bounds lifetime)
        root = seq(root, stem(obs_obj))
        # Also stem the sub-policy resource itself after its (copied) use, to model
        # "sub-agent code not persisted beyond this delegation" (for the copy case)
        root = seq(root, stem(so))

    # Supervisor integrates results (linear consumption of sub outputs)
    integrate = box(
        "SupervisorIntegrateResults",
        src=ctx_obj,
        tgt=ctx_obj,
        program_code=f"supervisor:{supervisor_name}:integrate",
    )
    root = seq(root, integrate)

    sd = StringDiagram(
        root=root,
        title=title,
        safety_explanation=(
            "Hierarchical pattern (illustrative geometry): Supervisor policy triangle forks (Δ) "
            "for its planning; each inner sub-agent is an explicit program triangle (resource) "
            "that the structure can fork (copy its definition for repeated/nested use) or consume "
            "linearly + stem. One-way sub-observations are stemmed after inner execution. "
            "This geometry surfaces nested policy-persistence surfaces (sup + subs) and "
            "the effect of guarding sub-agent code and outputs."
        ),
        morphism_steps=[],
    )

    d = Diagram(title=title)
    d.string_diagram = sd
    d.safety_explanation = sd.safety_explanation
    d.add_note("NEW PATTERN: Hierarchical — sub-agents as Δ/⊤ resources (copyable policies or linear delegation).")

    analysis = analyze_safety_geometry(sd)
    d.add_note(
        f"ANALYZER OUTPUT: policy_forks={analysis['policy_forks']}, "
        f"stems={analysis['stems']}, forks_by_type={analysis.get('forks_by_type')}, "
        f"stems_by_type={analysis.get('stems_by_type')}, "
        f"has_explicit_guards={analysis['has_explicit_guards']}, "
        f"sensitive_reaches={len(analysis.get('sensitive_reaches', []))}, "
        f"sensitive_persists={analysis.get('sensitive_persists')}"
    )
    d.add_note(
        "Safety geometry insight: sub-policy forks (classified under policy) coexist with sup forks; "
        "stems on SubObservation + SubAgentPolicy_* after use close some surfaces while allowing "
        "legitimate nested delegation."
    )

    return d


def build_reflexion_with_critic_diagram(
    tools: list[str] | None = None,
    cycles: int = 1,
    title: str | None = None,
) -> Diagram:
    """Builder for Pattern 2: Explicit reflection / self-critique with resource accounting.

    Actor part: standard ReAct-style with its Policy+Tools triangle + Δ forks + one-way query/obs.

    Then: one-way observation channel (distinct "ActorObservationToCritic" sensitive wire,
    no Δ) flows from actor trace into the critic scope.

    Critic has *its own independent policy fork*: a separate "CriticPolicy" triangle
    (not the same object as actor policy). This models the common case where the
    critic/reflector uses a different prompt, different few-shots, or a forked
    "critic head" of the policy.

    After critic consumes the one-way obs (under its policy copy), an explicit Stem
    on the obs path + a resource cost annotation for the critique step.

    Resource accounting: the critic path carries explicit "critic cost" in program_code
    and notes (can be read as parallel budget consumption in the model). A full
    graded resource wire could be added via tensor with a budget object, but the
    geometry already makes the extra compute surface of critique visible alongside
    the actor's.

    One-way boundaries: actor private state does not automatically Δ into critic;
    critic output (e.g. revision signal) can be modeled as linear back to actor
    memory or terminated.

    Why non-trivial:
    - Two distinct policy forks (actor + critic) in one diagram; analyzer will
      report multiple policy forks and "policy_copy_active" for both.
    - The critic's one-way input path is a classic info-flow boundary; the
      path-sensitive walk in SafetyAnalyzer will report whether actor sensitive
      (the obs) reaches the critic box *under* a critic policy copy.
    - Resource cost of critique is first-class (extra step that can be "spent"
      before or after dangerous actor actions in the trace).
    - Provides a fully structural realization of the critic pattern with explicit policy resources and termination.

    Used for modeling Reflexion, Self-Refine, constitutional AI critique loops,
    etc., with explicit accounting of the "critic tax" on resources and the
    additional persistence surface from the second policy copy.
    """
    if tools is None:
        tools = ["search", "calculator"]
    if title is None:
        title = f"Reflexion/Self-Critique with Separate Critic Policy (tools={tools}, cycles={cycles})"

    from ..core import Object
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
    from .reasoning import Diagram

    # Objects
    actor_policy_obj = Object("ActorPolicy+ToolDefs")
    critic_policy_obj = Object("CriticPolicy")
    ctx_obj = Object("ActorContext")
    obs_obj = Object("ActorObservation")
    critic_in_obj = Object("ActorObservationToCritic")  # the one-way boundary wire
    revision_obj = Object("CriticRevision")

    # === ACTOR TRACE (simplified 1-cycle for clarity; extendable) ===
    actor_tri = triangle("ActorPolicy+ToolDefs", actor_policy_obj)
    query_w = wire(Object("UserQuery"), "UserQuery (one-way to actor)")
    actor_entry = tensor(actor_tri, query_w)
    actor_root: Any = seq(actor_entry, fork(actor_policy_obj))

    # Reason
    reason_b = box(
        "ActorReason[0]",
        src=ctx_obj,
        tgt=ctx_obj,
        program_code="actor:reasoner_policy_copy_0",
    )
    actor_root = seq(actor_root, reason_b)

    # Tool(s)
    for tname in tools:
        tc_b = box(
            f"ActorTool[{tname}]",
            src=ctx_obj,
            tgt=obs_obj,
            program_code=f"tool_def:{tname}",
        )
        actor_root = seq(actor_root, tc_b)

    # Observe (one-way)
    obs_b = box("ActorObserve[0]", src=obs_obj, tgt=ctx_obj, program_code=None)
    actor_root = seq(actor_root, obs_b)
    # Stem the actor's internal obs after integration (standard guard)
    actor_root = seq(actor_root, stem(obs_obj))

    # === ONE-WAY BOUNDARY TO CRITIC ===
    # The observation is "sent" one-way to critic scope (no fork on actor side for this)
    # We model the boundary by tensoring a fresh one-way wire carrying the sensitive obs value.
    # (In a fuller trace the "value" would come from prior; here the wire introduces the infl.)
    critic_obs_wire = wire(critic_in_obj, "ActorObs (one-way to critic; no Δ)")
    # Now enter critic scope: critic's own policy triangle (separate from actor!) tensor the one-way obs
    critic_tri = triangle("CriticPolicy (self-critique fork)", critic_policy_obj)
    critic_entry = tensor(critic_tri, critic_obs_wire)
    # Chain the actor spine into the critic entry
    root = seq(actor_root, critic_entry)

    # Critic's independent Δ fork on *its* policy
    root = seq(root, fork(critic_policy_obj))

    # Critic step (with explicit resource cost annotation via program_code)
    critic_b = box(
        "CriticReflect+Score [cost:120 tokens, separate policy fork]",
        src=critic_in_obj,
        tgt=revision_obj,
        program_code="critic:reflect_policy_copy:cost120",
    )
    root = seq(root, critic_b)

    # Guard the one-way input after critic use + terminate critic revision linearly
    root = seq(root, stem(critic_in_obj))
    # Optional: stem on revision to model "critic feedback consumed once (or revision not persisted)"
    root = seq(root, stem(revision_obj))

    # Optional linear feedback path back (for self-correction in next actor cycle in fuller model)
    # Here we just show a merge box that could feed a revised plan (linear)
    feedback_b = box(
        "ApplyCriticRevision (linear feedback to actor memory)",
        src=ctx_obj,
        tgt=ctx_obj,
        program_code="apply_revision:linear",
    )
    root = seq(root, feedback_b)

    sd = StringDiagram(
        root=root,
        title=title,
        safety_explanation=(
            "Reflexion/critique pattern (illustrative): Actor has its Δ policy fork; "
            "observations cross to critic via dedicated one-way wire (no actor-side Δ on that path). "
            "Critic has a *distinct* policy triangle + its own Δ fork (models independent critic policy). "
            "Critique step carries explicit cost. Stems terminate the critic's one-way input and output. "
            "Analyzer sees two families of policy forks and whether actor obs reaches critic box "
            "under critic_copy_active (plus under actor policy if co-live)."
        ),
        morphism_steps=[],
    )

    d = Diagram(title=title)
    d.string_diagram = sd
    d.safety_explanation = sd.safety_explanation
    d.add_note("NEW PATTERN: Reflexion — distinct critic policy fork + one-way obs boundary + critique resource cost + stems on critic paths.")
    d.add_note("This makes the 'critic tax' (extra copied policy + extra compute) and the info-flow boundary explicit and analyzable.")

    analysis = analyze_safety_geometry(sd)
    d.add_note(
        f"ANALYZER OUTPUT: policy_forks={analysis['policy_forks']}, stems={analysis['stems']}, "
        f"forks_by_type={analysis.get('forks_by_type')}, "
        f"has_policy_sensitive_co_flow={analysis.get('flow_summary', {}).get('has_policy_sensitive_co_flow')}, "
        f"unguarded_sensitive_reaches={analysis.get('unguarded_sensitive_reaches')}"
    )

    return d


def build_multi_agent_coordination_diagram(
    agent_names: list[str] | None = None,
    use_shared_blackboard: bool = True,
    title: str | None = None,
) -> Diagram:
    """Builder for Pattern 3: Multi-agent coordination with clear information flow boundaries.

    Each agent has:
    - Its *private* policy triangle (e.g. "AgentA_Policy") — forks on one do not
      automatically affect the other (separate objects => separate influences).
    - Private channels (e.g. "PrivateThought_A") that are stemmed after the agent's
      local work to enforce isolation.

    Shared blackboard (if enabled):
    - A single "SharedBlackboard" Object with Δ forks. Both agents can receive
      copies into their context (modeled by forking the shared before each agent's
      work in the trace). This is copyable memory / common context.

    Private channels vs shared is the key distinction: shared uses explicit forks
    on the blackboard obj; privates never fork their thought wires.

    Coordination / consensus:
    - After private work, an explicit "ConsensusMerge" box.
    - Its input is modeled as tensor of the (post-stem) outputs from A and B
      (linear consumption, no auto-duplication of private results into the merge
      beyond what's explicitly passed).
    - The merge box can itself be a program (with triangle if we want the consensus
      rule to be copyable) or pure.
    - Post-merge, the result can be forked for broadcast back to agents, or stemmed.

    Stems on private paths after each local step + before/after merge ensure that
    private thoughts do not leak into the shared or the other agent's view except
    via the controlled merge point.

    Why non-trivial / high-signal for AI safety:
    - Directly models "debate", "mixture-of-agents", "swarm with blackboard",
      "private CoT + public summary" patterns.
    - The analyzer's path tracking + fork classification will report:
        * separate policy forks per agent
        * forks on "context" / blackboard vs no forks on private thoughts
        * whether any private sensitive reached the merge box (or leaked)
        * effect of stems on cross-boundary flow.
    - Explicit merge is the only "consensus" surface; reviewers can see if the
      merge box itself has a copied policy (the coordination rule) that could
      be attacked.
    - Clear visual + structural separation of shared (Δ) vs private (⊤/linear).

    Composes with the other patterns (e.g. one "agent" in the multi could be
    a hierarchical supervisor).
    """
    if agent_names is None:
        agent_names = ["AgentA", "AgentB"]
    if title is None:
        title = f"Multi-Agent Coordination (agents={agent_names}, shared_blackboard={use_shared_blackboard})"

    from ..core import Object
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
    from .reasoning import Diagram

    # Private policies (distinct objects => independent copy geometry)
    pol_a = Object(f"{agent_names[0]}_Policy")
    pol_b = Object(f"{agent_names[1]}_Policy")
    # Private channels (will be stemmed, no forks on them)
    priv_a = Object("PrivateThought_A")
    priv_b = Object("PrivateThought_B")
    # Shared (copyable)
    shared = Object("SharedBlackboard")
    # Merge / consensus objects
    proposal_a = Object("Proposal_A")
    proposal_b = Object("Proposal_B")
    consensus_obj = Object("ConsensusResult")

    # Entry: private policies as separate triangles (no cross Δ)
    tri_a = triangle(f"{agent_names[0]}_Policy", pol_a)
    tri_b = triangle(f"{agent_names[1]}_Policy", pol_b)
    # If shared, include its "initial value" as a triangle? or just wire; treat as basic data that forks.
    # For visibility, start with a shared "source" (can be a dummy triangle or just the object wire that gets forked).
    # Use a wire for the shared "state" that will be forked when accessed.
    shared_src = wire(shared, "SharedBlackboard (Δ-copyable when used)")

    # For parallel start: tensor the two agents' entries
    entry_a = tensor(tri_a, shared_src if use_shared_blackboard else wire(Object("I"), "no-shared"))
    entry_b = tensor(tri_b, wire(Object("I"), "agentB local"))  # placeholder; real shared access via forks later

    # To keep tree manageable we build a spine that "schedules" A then B then merge,
    # inserting forks on shared at the points of "access".
    # (True 2D parallel would use top-level tensor of two sub-spines; spine is sufficient
    # for influence tracking and produces clean linear+fork mermaid.)
    root: Any = seq(entry_a, fork(pol_a))  # A's private policy Δ

    # A works with possible shared copy
    if use_shared_blackboard:
        root = seq(root, fork(shared))  # Δ shared into A's context
    a_reason = box(
        f"{agent_names[0]}Reason (private)",
        src=priv_a,
        tgt=proposal_a,
        program_code=f"agent_a:private_reason",
    )
    root = seq(root, a_reason)
    # Stem private thought after local use (boundary)
    root = seq(root, stem(priv_a))
    if use_shared_blackboard:
        # After use, optionally stem the shared copy? But shared is meant to persist;
        # instead we leave the fork influence or stem a "local view". For model, stem
        # a derived private copy if we had one; here stem on a private-derived obj not needed.
        # To show boundary, we stem nothing extra on shared (it can be re-forked later).
        pass
    root = seq(root, stem(proposal_a))  # proposals are one-way into consensus

    # Now "switch" to B (approx scheduling; in real would be tensor parallel)
    # B also gets access to shared (another fork from the live shared influence)
    root = seq(root, fork(pol_b))
    if use_shared_blackboard:
        root = seq(root, fork(shared))  # second fork on shared for B
    b_reason = box(
        f"{agent_names[1]}Reason (private)",
        src=priv_b,
        tgt=proposal_b,
        program_code=f"agent_b:private_reason",
    )
    root = seq(root, b_reason)
    root = seq(root, stem(priv_b))
    root = seq(root, stem(proposal_b))

    # Explicit consensus / merge box. Input "from" the proposals (linear).
    # To represent the tensor-of-proposals feeding the merge, we can insert a
    # "join" simulation via seq of prior + a virtual tensor marker, but since
    # we stemmed, we use a box that "receives" the coordination.
    # For geometry we add a tensor( dummy proposal marker, ... ) but to keep
    # simple and analyzable, just the merge box after the stems; the prior stems
    # + live context carry the "proposal" infl (sensitive if private leaked).
    merge_box = box(
        "ConsensusMerge (explicit; only crossing point)",
        src=consensus_obj,
        tgt=consensus_obj,
        program_code="consensus_rule:merge_policy",  # the merge "policy" itself could be copyable
    )
    root = seq(root, merge_box)

    # Post-consensus: the result can be Δ broadcast (shared update) or linear.
    if use_shared_blackboard:
        root = seq(root, fork(shared))  # broadcast consensus back to blackboard
    else:
        root = seq(root, stem(consensus_obj))

    # Final stem on shared if we want to bound after the episode
    root = seq(root, stem(shared))

    sd = StringDiagram(
        root=root,
        title=title,
        safety_explanation=(
            "Multi-agent coordination pattern: Private per-agent policies (distinct triangles) "
            "fork independently. SharedBlackboard uses explicit Δ forks when 'read' by agents. "
            "Private thoughts are introduced on private objs and immediately stemmed after local "
            "reasoning (enforces no cross-leak). The only information crossing between agents is "
            "through the explicit ConsensusMerge box (which itself may carry a copyable rule). "
            "Stems + distinct objects create structural boundaries; analyzer quantifies exactly "
            "which forks are on shared vs private paths and whether privates reach the merge."
        ),
        morphism_steps=[],
    )

    d = Diagram(title=title)
    d.string_diagram = sd
    d.safety_explanation = sd.safety_explanation
    d.add_note("NEW PATTERN: Multi-agent — private policies + private channels (stemmed) vs shared blackboard (Δ forks at access); explicit merge as boundary control point.")
    d.add_note("Shared memory appears as context forks; privates appear as one_way_paths with stems. No automatic policy sharing across agents.")

    analysis = analyze_safety_geometry(sd)
    d.add_note(
        f"ANALYZER OUTPUT: policy_forks={analysis['policy_forks']}, stems={analysis['stems']}, "
        f"forks_by_type={analysis.get('forks_by_type')}, stems_by_type={analysis.get('stems_by_type')}, "
        f"sensitive_reaches count={len(analysis.get('sensitive_reaches', []))}, "
        f"flow_summary={analysis.get('flow_summary')}"
    )

    return d
