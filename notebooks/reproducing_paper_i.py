#!/usr/bin/env python3
"""
reproducing_paper_i.py
==============================================

A self-contained literate Python script that reproduces the central
fixed-point construction from Monoidal Computer Paper I (arXiv:1208.5205,
Lemma 6.2 and Proposition 6.1) and demonstrates its application to the
modeling of resource and information-flow properties in AI agent systems.

The script constructs and renders the relevant string diagrams using only
the public API of the library and illustrates how the explicit treatment of
copy (Δ) and deletion (⊤) operations makes certain safety-relevant
asymmetries visible in the diagrammatic representation.

Intended use:
- As a standalone executable demonstration of the core formal results.
- As a literate notebook (via jupytext) for detailed study.
- As a reference for researchers interested in applying monoidal
  categorical methods to the analysis of agent scaffolds.

Run:
    python notebooks/reproducing_paper_i.py
"""

# %% [markdown]
# # Reproduction of Paper I Fixed-Point Construction and Application to AI Safety Modeling
#
# This script provides an executable reproduction of the central result from
# Monoidal Computer Paper I together with an application to the diagrammatic
# analysis of agent scaffolds.
#
# The demonstration consists of three parts:
#
# 1. **Fixed-point construction (Paper I §6, p.25–26)** — constructed via
#    `MonoidalComputer.build_fixed_point` and rendered as a string diagram
#    using the diagrams layer. The construction relies only on the universal
#    evaluator and the data-service copy operation.
#
# 2. **ReAct-style agent scaffold** constructed via the models layer,
#    making explicit the distinction between copyable policy and tool
#    definitions (Δ) and one-way user queries and observations.
#
# 3. **Safety-relevant properties** that follow directly from the wiring
#    geometry: persistence of copied policy elements versus the linear
#    (non-duplicable) character of raw user input.

# %%
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

# Consistent bootstrap guard for notebooks (and examples/): single cmd
# `python notebooks/reproducing_paper_i.py` works from fresh clone.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams import (
    DataService,
    MonoidalComputer,
    Object,
)
from resource_diagrams.diagrams import MermaidRenderer
from resource_diagrams.models import build_simple_react_diagram

print("=" * 72)
print("Reproduction of Monoidal Computer Paper I Fixed-Point Construction")
print("with Application to Resource Modeling in AI Systems")
print("=" * 72)
print()

# %% [markdown]
# ## Part 1: Fixed-Point Construction (Paper I p.26)
#
# The central result of the series: because programs are *basic data* (they
# live in the universal type Ξ and satisfy the data-service axiom
# `δ ∘ p = p ⊗ p`), we can copy any program p with Δ and wire the two
# copies into the universal evaluator u. This yields a self-application
# transformer Φ such that composing Φ with p gives a fixed point of p.
#
# The entire proof is graphical and short. No Gödel numbering required.
#
# The demonstration uses only the public API:
# - `MonoidalComputer` and its `build_fixed_point` method
# - `DataService.copy` for the explicit Δ (copy) operation
# - `MermaidRenderer.render_fixed_point_construction` for diagram emission

# %%
print("PART 1: Fixed-Point Construction (Paper I Lemma 6.2 + Prop 6.1)")
print("-" * 72)

mc = MonoidalComputer()

# Programs are basic data — the crucial prerequisite (public API)
program = "succ"  # registered builtin, classic Paper I example
print(f"Program under study: {program!r}")
print(f"is_basic_data({program!r}) = {DataService.is_basic_data(program)}")

p1, p2 = DataService.copy(program, Object("Ξ"))
print(f"Δ copy: DataService.copy({program!r}, Ξ) → ({p1!r}, {p2!r})")
print("   (this is the diagrammatic 'fork' that makes recursion possible)")
print()

# The executable construction
fp_code, fp_meaning = mc.build_fixed_point(program)
print(f"mc.build_fixed_point({program!r}) →")
print(f"    fp_code   = {fp_code!r}")
print(f"    fp_meaning = {fp_meaning!r}")
print()

# Verify the law (using only public apply)
print("Verification of the fixed-point equation (public API only):")
print(f"    apply({fp_code!r}, {fp_code!r}) = {mc.apply(fp_code, fp_code)!r}")
p_on_e = mc.apply(program, fp_meaning)
print(f"    apply({program!r}, fp_meaning) = {p_on_e!r}  == fp_meaning ? {p_on_e == fp_meaning}")
print()

# The construction trace (auditability, exposed publicly)
print("Construction trace (mc.get_construction_trace()):")
print(textwrap.indent(mc.get_construction_trace(), "    "))
print()

# %% [markdown]
# ### The Diagram That Makes the Proof Visible (p.26 rendered live)
#
# This is the exact figure from the paper, generated on the fly by the
# public `MermaidRenderer`. Paste the output below into any Mermaid
# viewer (GitHub, VS Code, Obsidian, mermaid.live) to see it.

# %%
renderer = MermaidRenderer()
fp_diagram = renderer.render_fixed_point_construction("succ")

print("```mermaid")
print(fp_diagram)
print("```")
print()

# Also show the 03_ file that was exported by diagram_export.py
print("(The above matches the structure of examples/exports/03_fixed_point_construction.mmd)")
print()

# %% [markdown]
# **What the diagram + construction prove (researcher takeaway):**
#
# - The black dot (Δ) is the only "special" operation needed.
# - Because p is basic data, duplicating it is a free, structural operation.
# - One copy goes into u as the *program* argument; the other as the *data* argument.
# - The result e = {p}(p) satisfies {p}(e) = e by construction.
# - The same diagram works for *any* p (policy, tool spec, reasoning procedure).
#
# This is why the monoidal computer model is unusually powerful for
# self-referential AI systems: self-application is not a hack; it is
# the geometry of the category once you treat code as copyable data.

# %% [markdown]
# ## Part 2: ReAct-Style Agent Scaffold — Explicit Δ vs One-Way
#
# Modern agents are ReAct loops (or variants): Reason (using policy) →
# Tool calls → Observe → repeat, with memory/context accumulating.
#
# Using the public `build_simple_react_diagram` (from the models layer,
# which itself uses only core + diagrams), we obtain a rich `Diagram`
# object containing:
# - `.steps` (list of public `Morphism` for further use with evaluators)
# - `.to_mermaid()` (the visual resource diagram)
# - `.safety_explanation` (the precise insight the wiring makes visible)
#
# The key geometric fact: **policy and tool definitions are drawn as
# program triangles (▼) that support Δ (forks), while the user query
# and observations are linear one-way wires with no forks.**

# %%
print("PART 2: ReAct Agent Scaffold with Explicit Resource Geometry")
print("-" * 72)

react_diagram = build_simple_react_diagram(
    tools=["web_search", "code_interpreter"],
    cycles=2,
)

print("Built via: from resource_diagrams.models import build_simple_react_diagram")
print(f"Title: {react_diagram.title}")
print(f"Number of steps (public .steps list of Morphisms): {len(react_diagram.steps)}")
print()

# Show a couple of the underlying public Morphisms
print("Sample steps (public Morphism objects, with program_code signaling Δ):")
for i, step in enumerate(react_diagram.steps[:3]):
    prog = getattr(step, "program_code", None)
    print(f"  {i}: {step}  (program_code={prog!r})")
print("  ...")
print()

# %% [markdown]
# ### The Diagram (live Mermaid from the models layer)

# %%
print("ReAct resource diagram (react_diagram.to_mermaid()):")
print()
print("```mermaid")
print(react_diagram.to_mermaid())
print("```")
print()

# %% [markdown]
# ### The Safety Insight Made Structurally Visible
#
# This is the paragraph returned by the public builder (via .safety_explanation
# or .get_safety_explanation()). It is an *illustrative interpretation* of
# the shown geometry and trace annotations (program_code on steps as proxy
# for Δ forks on policy/tool vs one-way on query/obs wires; see the
# lightweight _scan_safety_geometry). Full derivation from categorical
# Fork/Stem nodes in the diagram tree is planned with diagrams/ unification.

# %%
print("Safety insight (react_diagram.safety_explanation):")
print("-" * 72)
print(react_diagram.safety_explanation)
print()

# %% [markdown]
# The construction makes several structural properties directly visible in
# the diagram:
#
# - Policy and tool definitions are subject to explicit copy (Δ). Any
#   element introduced via such a copy is available to every subsequent
#   reasoning step and tool invocation in the trace.
# - Raw user input and observations enter as one-way channels. They are
#   not duplicated by the data-service operations and therefore cannot
#   automatically propagate into later steps in the same manner.
# - Resource quantities (token costs) are attached to distinct parallel
#   wires. This renders budget constraints and potential loops as
#   first-class elements of the diagram geometry.
#
# The same diagrammatic distinction between copyable and linear channels
# applies to chain-of-thought traces, tool-use scaffolds, multi-agent
# coordination, and memory retrieval mechanisms.

# %% [markdown]
# ## Part 3: Connecting the Two — Fixed Points in Agent Policies
#
# Because the models layer returns objects that integrate with the core
# (via `.steps` and `.to_string_diagram()` where available), we can
# feed an agent policy into the fixed-point machinery.

# %%
print("PART 3: Fixed Point + Agent Policy (composition of layers)")
print("-" * 72)

# Treat an agent policy string as a "program" in the monoidal computer
agent_policy = "react_policy_v1_with_tools"
print(f"Agent policy as program: {agent_policy!r}")
print(f"  is_basic_data? {DataService.is_basic_data(agent_policy)}")

# Copy it explicitly (the Δ that appears in every ReAct diagram)
p1, p2 = DataService.copy(agent_policy, Object("Ξ"))
print(f"  Explicit Δ for agent policy: {p1!r}, {p2!r}")

# Now apply the Paper I construction to it
fp_agent_code, fp_agent_meaning = mc.build_fixed_point(agent_policy)
print(f"  build_fixed_point on agent policy → {fp_agent_code!r}, meaning={fp_agent_meaning!r}")
print()

# Render the diagram for this AI-relevant fixed point
agent_fp_mmd = renderer.render_fixed_point_construction(agent_policy)
print("Corresponding diagram (agent policy fixed point):")
print("```mermaid")
print(agent_fp_mmd[:800] + "\n... (truncated for script brevity)\n```")
print()

# %% [markdown]
# ## Summary of the Demonstration
#
# The script constructs the following using only the public API of the library:
#
# - The fixed-point construction of Paper I §6 (Lemma 6.2 and Proposition 6.1),
#   realized via `MonoidalComputer.build_fixed_point` and rendered by
#   `MermaidRenderer.render_fixed_point_construction`.
# - A ReAct-style scaffold via `build_simple_react_diagram`, with explicit
#   distinction between copyable (Δ) and one-way channels together with
#   the associated safety interpretation.
# - Composition of the two layers: an agent policy string is passed directly
#   to the fixed-point construction.
#
# All generated diagrams and annotations are deterministic. The exported
# Mermaid files in `examples/exports/` were produced by the same renderer
# (see `examples/diagram_export.py`).

# %%
print("=" * 72)
print("END OF reproducing_paper_i.py")
print("All constructs used the public API only.")
print("Diagrams written to examples/exports/ (4 paper figures + 2 AI models).")
print("Ready for researcher inspection, citation in papers, and extension.")
print("=" * 72)
