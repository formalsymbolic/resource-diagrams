# Recipe: Transcribing LangGraph Agents to Resource Diagrams

This recipe shows how to turn a LangGraph `StateGraph` (or any similar stateful agent graph) into a Resource Diagram so that policy/tool copying (Δ) versus one-way channels become explicit, countable structural features.

The goal is **review and audit**, not execution. The resulting diagram + `analyze_safety_geometry` output can be attached to PRs, design docs, or red-team reports.

## Why This Matters for LangGraph Users

LangGraph makes it easy to bind tools and system prompts once at graph construction time and have them persist across nodes and runs. That binding is a Δ (copy) operation on program data. User inputs and tool observations are typically one-way. When these distinctions are left implicit in Python objects and state dicts, it becomes hard to see the exact surfaces available for prompt injection, policy exfiltration, or unintended persistence.

Resource Diagrams make the same distinctions first-class categorical geometry (Triangle + Fork for the bound policy, Stem for explicit termination of one-way channels) and give you machine-readable counts.

## Core Mapping (common patterns)

| LangGraph construct                  | Resource Diagram equivalent                          | Safety reading |
|--------------------------------------|------------------------------------------------------|----------------|
| `StateGraph(tools=..., prompt=...)` or `bind_tools` at construction | `Triangle("BoundPolicy+ToolDefs")` followed by `Fork(Δ)` | The single source of policy copies that will reach every downstream node |
| `.add_node("agent", ...)` / reasoner | `Box("AgentNode", program_code=...)`                 | Receives a copy of the policy triangle |
| `ToolNode(tools)` or tool executor   | `Box("ToolNode[...]", program_code="tool_def:...")`  | Tool definitions are themselves copied data |
| `add_edge(START, "agent")`           | `seq( tensor(policy_tri, user_wire), fork )`         | Entry point where the Δ becomes active |
| Conditional / observation edges      | `seq(..., observe_box, stem(obs_obj) or wire)`       | One-way feedback path; presence of `Stem` = guarded |
| `graph.compile()`                    | The root `StringDiagram` + `morphism_steps`          | Complete structural artifact for the analyzer |

The `program_code` attribute on boxes is the signal that a step carries copied policy/tool data (exactly the information `DataService.copy` would duplicate in the underlying model).

## Minimal Transcription Walkthrough

See `examples/langgraph_style_transcription.py` for a complete, self-contained runnable example that produces the diagram for a representative tool-calling graph (entry policy binding + reasoner + tool node + guarded observation).

Running it prints:
- The Mermaid source of the structural diagram (entry fork on the policy triangle, explicit Stem on the observation path).
- The analyzer output (`policy_forks`, `stems`, `has_explicit_guards`, etc.).
- A comment block showing the corresponding LangGraph sketch and what the diagram makes visible that the source code does not.

## Recommended Review Practice (for maintainers)

1. Identify the critical graphs in your LangGraph-based framework or application (especially those that bind tools, long-lived system prompts, or memory).
2. Transcribe the construction-time bindings and the main node/edge paths using the mapping above (start with the entry fork + one representative cycle).
3. Assert on the analyzer results in your review checklist or CI:
   - `has_structural_policy_copy` is expected for legitimate tool reuse.
   - For graphs handling secrets or PII: `has_explicit_guards` or `stems > 0` on sensitive paths.
   - Large deltas in `one_way_paths` after a change are worth a second look.
4. Attach the generated Mermaid (or the `.string_diagram`) to the PR description.

This turns an otherwise opaque "we added a new memory node" change into a reviewable structural delta.

## Extending the Transcription

- Add more nodes by additional `seq(..., box("NextNode", program_code=...))`.
- Model conditional branches with `Tensor` (parallel possible futures) or multiple alternative `Sequential` sub-diagrams.
- For memory that is explicitly copied across turns, insert additional `Fork` nodes on the state object.
- Use the guarded contrast builder (`build_guarded_vs_unguarded_contrast`) as a subroutine when the LangGraph path mixes persistent policy with transient user data.

All of the above remains pure Python and self-contained.

## Scope Note

This recipe is a **transcription and review aid**, not a LangGraph execution or interoperability layer. It is deliberately free of any dependency on `langgraph`, `langchain`, or LLM providers so that the diagrams can be generated and inspected in any environment (including air-gapped review machines). The value is in the structural visibility and the analyzer metrics, not in round-tripping runnable graphs.

If you maintain a LangGraph-based agent framework and would like to contribute a richer set of transcription helpers or example graphs, open an issue with the "modeling_pattern" template.

## References

- `examples/langgraph_style_transcription.py` — the canonical self-contained transcription.
- `examples/guarded_contrast.py` — the distilled guarded/unguarded primitive.
- `src/resource_diagrams/diagrams/safety.py` — `analyze_safety_geometry`.
- `docs/gallery.md` — curated visual examples including the LangGraph-style transcription.
