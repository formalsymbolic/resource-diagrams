# Diagram Gallery: Agent Security Surfaces

This gallery highlights diagrams that make **policy and tool-definition copying (Δ forks on program triangles) versus one-way channels** visible as structural security surfaces.

These are the core artifacts that demonstrate the practical value of Resource Diagrams for AI safety and agent oversight.

## Core Examples

### ReAct / Tool-Use Loop (Primary Demonstration)
- **File**: `examples/react_loop.py` (runnable with `python examples/react_loop.py`)
- **Exports**: `examples/exports/05_react_agent_scaffold.mmd`
- **Key Insight**: Policy/tool definitions fork via Δ into every reasoning and tool step. User queries and observations are one-way (no automatic duplication). This geometry directly corresponds to persistence and exfiltration risks in agent scaffolds. Now also exposes a real `StringDiagram` via the models layer.
- **Safety Text** (illustrative of the geometry):
  > This diagram makes visible that the tool definition (program triangle) can be copied into the context (via Δ) while the user query flows only one way (no Δ on the query wire). ...
- Now also exposes a full `StringDiagram` with real Fork/Stem geometry + the new `analyze_safety_geometry` structural analyzer for machine-readable insights.

### Reflexion / Self-Critique Extension
- **File**: `examples/reflexion_loop.py`
- **Key Insight**: Extends the core hook — policy forks into both the main actor and a critic/reflector. Feedback remains one-way, creating additional persistence vectors common in self-improving agent designs.

### Guarded vs Unguarded One-Way Channels (Core Hook, Quantified)
- **File**: `examples/guarded_contrast.py` (runnable with `python examples/guarded_contrast.py`)
- **Key Insight**: The *only* structural difference between the two diagrams is the presence (guarded) or absence (unguarded) of an explicit Stem (⊤) on the sensitive one-way wire after use. The SafetyAnalyzer reports the delta directly (`stems`, `has_explicit_guards`) while policy Δ forks remain identical. This is the diagrammatic act of guarding made machine-readable.

### LangGraph-Style Graph Transcription
- **File**: `examples/langgraph_style_transcription.py` + `docs/recipe_langgraph.md`
- **Key Insight**: A common LangGraph `StateGraph` (entry binding of tools/prompt + nodes + conditional observation edges) transcribed to a `StringDiagram`. The initial `Fork(Δ)` on the policy triangle corresponds to the persistent binding performed at `graph.compile()` time. The recipe gives a mapping table and review checklist for LangGraph users and maintainers of LangGraph-based frameworks. The analyzer produces the same policy-fork / one-way metrics as the native builders.
- **Audience expansion**: Directly usable by the large community building production agents on LangGraph without requiring any LangGraph runtime in the review environment.
- **Safety geometry delta** (from `analyze_safety_geometry`):
  - Unguarded: stems=0, has_explicit_guards=False (open persistence surface)
  - Guarded:   stems=1, has_explicit_guards=True (channel terminated after use)
- Directly usable in design reviews and red-team reports for any scaffold that routes secrets, credentials, or observations into tool/policy contexts.

### Information Flow Contrast
- **File**: `examples/info_flow_diagram.py`
- **Key Insight**: Explicit contrast between copyable internal state (Δ) and one-way user secrets (⊤ / linear flow).

### Fixed-Point Construction (Paper I Foundation)
- **File**: `examples/fixed_point_demo.py`
- **Exports**: `examples/exports/03_fixed_point_construction.mmd`
- **Key Insight**: Because programs are basic data (supporting Δ), self-application and fixed points become diagrammatically obvious. Relevant to self-referential agent policies.

### Resource Accounting
- **File**: `examples/resource_trace.py`
- **Key Insight**: Token budgets and costs as first-class parallel wires that interact with copied policy paths.

## How to Explore
All diagrams above are generated from the public API. Run the corresponding example scripts from a fresh clone — no installation required thanks to bootstrap guards.

To build your own:
```python
from resource_diagrams.models import build_simple_react_diagram
d = build_simple_react_diagram(tools=["search", "code"], cycles=2)
print(d.to_mermaid())
print(d.safety_explanation)
```

## Contributing New Diagrams
See `CONTRIBUTING.md` and the "modeling_pattern" issue template. We particularly value new patterns that make Δ vs. one-way distinctions (or other security-relevant geometry) clearer and more structural.

For detailed examples of modeling information flow, see [diagrammatic-modeling-of-agent-information-flow.md](diagrammatic-modeling-of-agent-information-flow.md).

For the full catalog of paper figures (01–04), see `examples/diagram_export.py`.
