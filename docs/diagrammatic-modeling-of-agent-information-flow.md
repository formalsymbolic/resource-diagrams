# Diagrammatic Modeling of Agent Information Flow

This document illustrates how Resource Diagrams can be used to model and analyze the information-flow structure of agent systems, with particular attention to the distinction between copyable program elements (policies and tool definitions) and linear data channels (user inputs and observations).

The examples and patterns are intended for researchers and engineers interested in precise, visual representations of agent architectures. While the formalism has natural applications to questions of information security and oversight, the primary goal is to explore the expressive power of string diagrams in this domain.

## Motivation

In many agent architectures, policy and tool definitions behave as copyable data, while user-provided inputs and intermediate observations typically do not. The string diagram formalism makes this distinction explicit through the use of Fork (Δ) and Stem (⊤) nodes. This can help clarify the lifetime and potential reach of different kinds of information within a system.

Resource Diagrams provides both the underlying categorical primitives and higher-level modeling tools for constructing such diagrams, along with support for structural analysis of the resulting graphs.

## Illustrative Patterns

The following examples demonstrate how common agent design choices appear in diagrammatic form. These are not presented as an exhaustive catalog of vulnerabilities, but rather as illustrations of how the formalism renders certain architectural decisions visible.

### 1. Unguarded Policy + Sensitive Data Co-location
**Geometry**: Policy triangle forks (Δ) into a step that also receives a one-way user secret or observation with no subsequent Stem.

**Observation**: When a one-way channel carrying sensitive data is not explicitly terminated, the same value may remain available to subsequent steps that also receive copies of policy or tool definitions.

**Example**: See `examples/guarded_contrast.py`.

**Alternative modeling**: The guarded version in the same example inserts an explicit Stem on the sensitive path after use. This produces a visibly different diagram geometry.

### 2. Tool Definition Persistence
**Geometry**: Tool definitions are modeled as program triangles that fork into every reasoning and tool-invocation step.

**Observation**: Tool definitions that are bound once and then copied into multiple reasoning and execution steps appear in the diagram as a Triangle followed by one or more Fork nodes. This structure makes the extent of their duplication explicit.

This pattern is common in ReAct-style loops and tool-calling graphs. The diagram can be used to compare designs that copy tool definitions broadly versus those that maintain narrower scoping.

### 3. Memory / Context as Unbounded Policy Carrier
**Geometry**: Memory state objects that receive both policy forks and one-way observations, then fork again on the next cycle.

**Risk**: Observations that should be transient become part of the persistent policy-carrying context.

**Mitigation**: Use separate objects for "policy-carrying context" vs "current-turn observations" and apply Stems to the latter.

## Modeling Choices

When constructing diagrams of agent systems, several recurring modeling decisions arise:

- Whether to represent the termination of a one-way channel explicitly using a Stem node.
- How narrowly to scope the objects that carry policy versus transient data.
- Whether to produce contrasting diagrams of the same scenario under different assumptions about copying and deletion.

The `build_guarded_vs_unguarded_contrast` function and the transcription examples in the `examples/` directory illustrate these choices.

## Worked Example: LangGraph-style Tool Graph

See `examples/langgraph_style_transcription.py` for a complete, runnable transcription of a common StateGraph pattern (entry policy+tool binding as a Triangle that forks, nodes as Boxes, observation path terminated with a Stem).

Running the example and calling:

```python
from resource_diagrams import generate_security_report
report = generate_security_report(sd)
print(report.overall_risk)
print(report.findings)
```

produces structured findings that can be pasted directly into a review comment or security ticket.

## Usage

Diagrams can be constructed programmatically using the builders in `resource_diagrams.models` or the lower-level combinators in `resource_diagrams.diagrams`. The resulting `StringDiagram` objects can be rendered to Mermaid or inspected using the structural analysis functions.

The examples directory contains several complete, self-contained scripts demonstrating these capabilities on common agent patterns. All run from a fresh clone with no additional dependencies.

## Limitations

- This is structural analysis of the *model* of an agent, not of its runtime behavior or the underlying LLM.
- The analyzer uses conservative heuristics. A "medium" or "high" finding is a prompt for human review, not an automatic vulnerability.
- Transcriptions of real codebases are manual and best-effort. They are aids to thinking, not formal proofs.

## Related Artifacts

- `examples/guarded_contrast.py` — distilled demonstration of the core guard operation.
- `examples/langgraph_style_transcription.py` + `docs/recipe_langgraph.md`
- `src/resource_diagrams/diagrams/safety.py` — `generate_security_report` and `SecurityReport`
- `docs/gallery.md` — visual catalog of the key patterns.

This playbook is deliberately narrow. Its goal is to make one high-leverage distinction (policy copying lifetime vs one-way channel lifetime) cheap to audit in agent code.