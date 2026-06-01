"""
resource_diagrams.models

Higher-level, example-driven modeling layer for common AI/agent constructs
expressed as resource diagrams.

This subpackage sits on top of the categorical core (Object, Morphism,
DataService, MonoidalComputer) and the (assumed) diagrams construction
primitives. It provides ergonomic builders and classes for:

- Explicit resource modeling (tokens, compute steps, information channels
  with copy/delete semantics for leakage analysis, one-way transforms).
- Agent scaffolds (ToolCall morphisms with attached costs, ReAct-style
  loops as composite traces, MemoryState with explicit Δ for context copying).
- Lightweight reasoning traces with info-flow annotations.

All constructs are for *modeling and visualization only*. They produce
sequences of core Morphisms plus diagrammatic representations (Mermaid)
that make resource properties, control flow, and potential safety issues
legible. No execution engine, no runtime agent loop, no external deps.

See ARCHITECTURE.md (models/ section), VISION.md, and the examples/ and notebooks/
directories for usage patterns and the intended role of this layer as the bridge
between the formal categorical core and practical AI safety modeling concerns.

Quickstart
----------

    from resource_diagrams.models import (
        build_simple_react_diagram,
        model_token_accounting,
        basic_info_flow_diagram,
        InformationChannel,
    )
    from resource_diagrams.core import Object, Morphism

    # 1. Build a ReAct-style trace as diagram (primary modeling pattern)
    d = build_simple_react_diagram(tools=["web_search", "calculator"], cycles=2)
    print(d.to_mermaid())
    print("\nSafety insight from the diagram:")
    print(d.safety_explanation)

    # 2. Resource accounting on a trace (primary modeling pattern)
    trace_costs = [("reason", 45), ("tool_call:search", 120), ("observe", 30)]
    d2 = model_token_accounting(trace_costs, total_budget=500)
    print(d2.to_mermaid())

    # 3. Info-flow annotation highlighting leakage risk via copy semantics
    chan = InformationChannel("internal_state", copyable=True)
    d3 = basic_info_flow_diagram(chan)
    print("Diagram highlights copy on sensitive channel:", "Δ" in d3.to_mermaid())

The diagrams use standard Mermaid `graph TD` syntax (wires as arrows,
boxes for computation steps, ▼-style labels or subgraphs for program
triangles representing copyable policy/tool data). Paste the output
directly into any Mermaid renderer (GitHub, VS Code, etc.).

Key Safety-Relevant Idioms Highlighted
--------------------------------------

- **Copy (Δ) vs delete (⊤) on data wires**: Policies, tool definitions,
  and prompts are "basic data" (DataService.is_basic_data) and therefore
  freely duplicable. This is powerful for self-reference but creates
  persistence and leakage surfaces. User queries and private observations
  are typically modeled as one-way (no Δ) or explicitly deleted after use.
  The diagram makes the difference visible at a glance.

- **Resource wires as first-class**: Token budgets, compute steps, and
  information channels appear as parallel or graded wires alongside
  data flow. Depletion and accounting become structural, not hidden in
  logs.

- **One-way / non-invertible transforms**: Tool responses or "observe"
  steps can be modeled as non-invertible (no program triangle for the
  inverse), surfacing "information hardness" or the difficulty of
  recovering original secrets from outputs.

- **ReAct loop structure**: The classic reason → tool → observe cycle
  is a composite with explicit memory/context copying at each step.
  The resulting diagram renders the points at which a copied policy element becomes available to subsequent steps.
  steps or where a single poisoned observation can propagate.

Example insight (from build_simple_react_diagram):
    "Illustrative interpretation of the shown geometry (and trace annotations):
    This diagram makes visible that the tool definition (program triangle
    with ▼) can be copied into the context (via Δ) on every cycle while
    the user query flows only one way into the reasoner and is not
    duplicated into the tool call arguments or memory state. This
    asymmetry highlights a potential vector for policy exfiltration
    (the copied tool spec can be echoed in observations) versus
    protection of the raw user query from tool-side leakage."

    All such .safety_explanation values (and .get_safety_explanation()) are
    explicitly labeled as interpretive of the diagram's annotations and
    step structure (program_code presence proxies Δ; see Diagram._scan... ).

Integration Notes
-----------------
- Builders return instances of `Diagram` (thin facade in this subpackage,
  or the enhanced diagrams.StringDiagram).
  The implementation constructs StringDiagram trees (using fork, stem,
  triangle, seq, tensor from diagrams/) so that Δ policy copies vs one-way
  flows are structural geometry in the diagram (enabling full derivation).
  Plus .steps (core.Morphism for evaluators), .to_mermaid() (delegates to
  official renderer), .safety_explanation (illustrative of real wiring).
- Composes naturally: `d.steps` for core/evaluators; `d.to_string_diagram()`
  returns the real diagrams.StringDiagram (full categorical tree). Models
  layer consumes diagrams/ for rendering + construction (single source of
  truth; no more parallel emitter).
- See diagrams/ for the primitives and renderer; models/ for the high-level
  AI safety idiom builders (ReAct, token accounting, info-flow).
- Pure stdlib only. No external agent frameworks or execution engines.
  frameworks.

This layer evolves faster than core per ARCHITECTURE.md. Prioritize
high-signal safety patterns (ReAct + explicit resource accounting)
over breadth.
"""

from __future__ import annotations

from .agents import (
    AgentStep,
    GuardedContrast,
    MemoryState,
    ReActCycle,
    ToolCall,
    build_guarded_vs_unguarded_contrast,
    build_simple_react_diagram,
)
from .reasoning import (
    Diagram,
    ReasoningTrace,
    basic_info_flow_diagram,
    info_flow_annotation,
)
from .resources import (
    ComputeStep,
    InformationChannel,
    OneWayTransform,
    TokenBudget,
    model_token_accounting,
)

__all__ = [
    # Core modeling primitives
    "Diagram",
    "TokenBudget",
    "ComputeStep",
    "InformationChannel",
    "OneWayTransform",
    "ToolCall",
    "AgentStep",
    "MemoryState",
    "ReActCycle",
    "ReasoningTrace",
    # High-value worked example builders (ReAct + resource accounting focus)
    "build_simple_react_diagram",
    "model_token_accounting",
    "basic_info_flow_diagram",
    "info_flow_annotation",
    # Guarded contrast (new applied pattern for explicit one-way guarding)
    "GuardedContrast",
    "build_guarded_vs_unguarded_contrast",
]

# Version of the modeling layer (independent of top-level for now)
__version__ = "0.1.0-models"
