#!/usr/bin/env python3
"""
LangGraph-style stateful agent transcribed to a Resource Diagram.

This example shows a minimal, self-contained transcription of a common
LangGraph pattern (StateGraph with a persistent policy/tool binding at
entry + tool nodes + observation feedback) into the categorical string
diagram representation.

NO LangGraph dependency is required or used. The script is 100% runnable
from a fresh clone using only this library.

Purpose (for LangGraph users and maintainers of LangGraph-based frameworks):
- Make the policy/tool copying (Δ) at graph construction time *visible*
  as a Fork on a program triangle.
- Make one-way user inputs and tool observations explicitly linear
  (or guarded with Stem) rather than implicitly carried in opaque state.
- Give a concrete artifact that can be dropped into a PR or design review
  for any graph that binds tools or system prompts.

Mapping (one common pattern):

LangGraph concept                  | Resource Diagram equivalent
-----------------------------------|--------------------------------------------
StateGraph(tools=..., prompt=...)  | Triangle("Policy+Tools") ; Fork(Δ)
.add_node("agent", ...)            | Box("AgentReason")
.add_node("tools", ...)            | Box("ToolCall[...]")  [program_code present]
.add_edge(START, "agent")          | Entry tensor + seq
.add_conditional_edge(...)         | Seq with possible Stem on observe path
.compile()                         | The full StringDiagram (structural + trace)

The analyzer then reports the structural safety geometry (policy forks vs
one-way paths) for the transcribed graph.

See docs/recipe_langgraph.md for the full guide and more mappings.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams import Object
from resource_diagrams.diagrams import (
    StringDiagram,
    box,
    fork,
    seq,
    stem,
    tensor,
    triangle,
    wire,
)
from resource_diagrams.diagrams.safety import analyze_safety_geometry


def build_langgraph_style_diagram() -> StringDiagram:
    """Build a representative transcription of a LangGraph tool-calling graph.

    Entry: policy triangle (the "tools" and "prompt" bound once at compile)
           forks via Δ so every node can see the same definitions.

    Nodes: reason step + tool invocation (both carry program_code so they
           are recognized as policy-derived).

    Feedback: observation path ends with explicit Stem (guarded style).
    """
    policy_obj = Object("Policy+Tools")
    user_obj = Object("UserInput")
    state_obj = Object("AgentState")

    # The "compiled graph" entry point: policy as copyable data
    policy_tri = triangle("BoundPolicy+ToolDefs (graph entry)", policy_obj)
    user_w = wire(user_obj, "User query (one-way into graph)")

    # Entry fork — this is the diagrammatic counterpart of binding tools/prompt
    # once at StateGraph(..., tools=tool_list) time and reusing across runs/nodes.
    entry = tensor(policy_tri, user_w)
    after_fork = seq(entry, fork(policy_obj))

    # Node 1: the main agent / reasoner (receives copied policy)
    reason = box(
        "AgentNode (reason + decide)",
        src=state_obj,
        program_code="langgraph_bound_policy",
    )

    # Node 2: tool executor (also receives copied tool definitions)
    tool = box(
        "ToolNode[web_search, calculator]",
        src=state_obj,
        program_code="langgraph_tool_def:web_search",
    )

    # Observation / tool result returns one-way; we explicitly stem it
    # (the guarded transcription choice; an unguarded version would omit this).
    observe = box("ObserveResult", src=state_obj, tgt=state_obj)
    guard = stem(Object("Observation"))

    # Compose the representative trace
    root = seq(after_fork, reason)
    root = seq(root, tool)
    root = seq(root, observe)
    root = seq(root, guard)

    sd = StringDiagram(
        root=root,
        title="LangGraph-style Tool Graph (transcribed)",
        safety_explanation=(
            "Illustrative transcription of a typical LangGraph StateGraph. "
            "The initial Δ fork on the policy triangle corresponds to the "
            "persistent binding of tools and system prompt at graph construction. "
            "Each node receives the copied definitions. The final Stem on the "
            "observation path is an explicit guard choice in the transcription."
        ),
        metadata={"source": "langgraph_style_transcription"},
    )
    return sd


def main() -> None:
    print("=" * 72)
    print("RESOURCE DIAGRAMS — LangGraph-style Transcription (self-contained)")
    print("=" * 72)
    print()
    print("This builds a pure categorical diagram equivalent to a common")
    print("LangGraph StateGraph pattern (entry policy binding + tool nodes).")
    print("No langgraph package is imported or required.")
    print()

    sd = build_langgraph_style_diagram()

    print("--- Mermaid (structural view of the transcribed graph) ---")
    print(sd.to_mermaid())
    print()

    analysis = analyze_safety_geometry(sd)
    print("--- Structural safety analysis ---")
    print(analysis)
    print()

    print("--- LangGraph mapping notes (for users who have LangGraph) ---")
    print(
        """
# Equivalent LangGraph sketch (for mental / manual transcription only):

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# The "policy + tools" bound here become the Triangle + Fork(Δ) in the diagram
tools = [web_search, calculator]
graph = StateGraph(AgentState)
graph.add_node("agent", make_agent(tools=tools, system_prompt=...))
graph.add_node("tools", ToolNode(tools))
graph.add_edge(START, "agent")
graph.add_conditional_edge("agent", should_use_tool, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")
compiled = graph.compile()

# What the diagram makes visible that the LangGraph source does not:
# - The Δ copy of the bound tools/prompt into every node invocation.
# - The one-way lifetime of user input and tool observations (especially
#   when you choose to insert an explicit "guard" / cleanup step).
# - The structured count of policy forks vs one-way paths via analyze_safety_geometry.

# Recommended review practice:
#   1. Run your graph construction.
#   2. Transcribe the entry binding + nodes + observation paths as above.
#   3. Assert on analyzer["has_explicit_guards"] or policy_forks for critical paths.
"""
    )

    print("=" * 72)
    print("langgraph_style_transcription.py complete.")
    print("See docs/recipe_langgraph.md for the expanded guide.")
    print("=" * 72)


if __name__ == "__main__":
    main()
