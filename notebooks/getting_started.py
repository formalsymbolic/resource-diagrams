#!/usr/bin/env python3
"""
getting_started.py
======================

A literate, runnable introduction to Resource Diagrams.

This script walks through the core concepts from the Monoidal Computer
framework (Pavlovic et al.) as implemented in the library, showing both
the Python API and the diagrammatic intuition.

It is designed to be:
- Read top-to-bottom as documentation
- Run directly: `python notebooks/getting_started.py` (single command from fresh clone)
- Converted to a Jupyter notebook (the # %% markers delineate cells)

The examples use only the public API and produce real output.
"""

# %% [markdown]
# # Getting Started with Resource Diagrams
#
# Resource Diagrams brings the string-diagram language of monoidal category
# theory — specifically the "Monoidal Computer" model of Dusko Pavlovic —
# into practical Python code for modeling resources and structure in AI
# and agent systems.
#
# The central idea is that programs, prompts, policies, and computations
# can be treated as first-class *data* that can be copied, deleted,
# specialized, and composed, all while remaining inspectable in a
# visual, geometric language (string diagrams).

# %%
from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap guard (consistent with examples/): makes
# `python notebooks/getting_started.py` work on fresh clone
# (before pip -e . or PYTHONPATH). Place before any resource_diagrams import.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams import (
    DataService,
    MonoidalComputer,
    Morphism,
    Object,
    diagrams,  # the diagrams layer
)
from resource_diagrams.models import build_simple_react_diagram

print("Resource Diagrams version:", "0.1.0 (from __init__)")
print("diagrams layer version:", getattr(diagrams, "__diagrams_version__", "n/a"))
print()

# %% [markdown]
# ## 1. Objects and Morphisms — the basic vocabulary
#
# In the categorical model, objects represent types of data, states,
# resources, channels) and *morphisms* (computations, transformations,
# agent steps, tool calls).

# %%
A = Object("UserGoal")
B = Object("Plan")
C = Object("Action")

print("Objects:", A, B, C)

# A simple morphism (a Python callable is supplied for simulation)
def dummy_plan(goal: str) -> str:
    return f"plan_for({goal})"

plan_step = Morphism("plan", A, B, impl=dummy_plan, program_code="plan_v1")
print("Morphism:", plan_step)
print()

# %% [markdown]
# ## 2. Data Services — copy (Δ) and delete (⊤)
#
# The data-service operations provide the mechanism by which programs and
# other elements can be treated as first-class data. When an object is
# classified as basic data, it may be explicitly duplicated via the copy
# operation (Δ) and discarded via the delete operation (⊤).

# %%
policy = "system_prompt: be helpful, refuse harmful requests"
print("Original policy:", policy)

p1, p2 = DataService.copy(policy, Object("Ξ"))
print("After copy:", p1, "and", p2)

DataService.delete(p2, Object("Ξ"))
print("After deleting one copy, the other remains:", p1)
print("is_basic_data(policy):", DataService.is_basic_data(policy))
print()

# %% [markdown]
# The corresponding string diagram (comonoid) is:
#
# ```mermaid
# graph TD
#     A -->|Δ| Fork
#     Fork --> A2
#     Fork --> A3
# ```
#
# (Full versions are in `diagrams/04_data_services_comonoid.mmd` and
#  the export example.)

# %% [markdown]
# ## 3. The Monoidal Computer — universal evaluator u and partial evaluator s
#
# The heart of the model (Paper I, Def 4.1):
#
# - `u` (apply): given a program (as data) and an input, produces output.
# - `s` (specialize): given a program and a fixed argument, returns a
#   new program that has that argument "baked in".

# %%
mc = MonoidalComputer()

print("Registered core programs:", list(mc._programs.keys()))  # for illustration

result = mc.apply("succ", 41)
print("apply('succ', 41) =", result)

specialized = mc.specialize("succ", 5)
print("specialize('succ', 5) =", specialized)
print("apply(specialized, 10) =", mc.apply(specialized, 10))
print()

# %% [markdown]
# Diagrammatically, `apply(program, input)` corresponds to:
#
#     input
#       |
#       v
#   [ program triangle ]
#       |
#      [ u ]
#       |
#       v
#     output
#
# See `diagrams/02_universal_evaluator_law.mmd`.

# %% [markdown]
# ## 4. The Fixed-Point Construction (Paper I p.26)
#
# Because programs are classified as basic data, the copy operation (Δ)
# may be applied to them. This permits the construction of a
# self-application transformer Φ from the data-service copy operation and
# the universal evaluator. Composition of Φ with an arbitrary program p
# yields a fixed point of p.

# %%
fp_code, fp_meaning = mc.build_fixed_point("succ")
print("build_fixed_point('succ') →", fp_code, "meaning=", fp_meaning)

# The full graphical proof is in examples/fixed_point_demo.py
# and diagrams/03_fixed_point_construction.mmd
print()

# %% [markdown]
# ## 5. Modeling a Resource-Aware Computational Step
#
# The core types suffice to represent a simple agent step that both
# consumes a resource and operates on a copyable policy element.

# %%
PolicyObj = Object("Policy")
StepInput = Object("StepInput")
StepOutput = Object("StepOutput")
Tokens = Object("Tokens")

policy_copy_for_step, _ = DataService.copy("agent_policy", Object("Ξ"))

def step_impl(x):
    return "acted_on(" + str(x) + ")"

agent_step = Morphism(
    "agent_step",
    StepInput,
    StepOutput,
    impl=step_impl,
    program_code=policy_copy_for_step,
)

print("Agent step morphism with embedded policy copy:")
print("  ", agent_step)
print("  program_code (the copied policy):", agent_step.program_code)
print()

# %% [markdown]
# ## 6. Next Steps
#
# - Run the standalone examples:
#     python examples/fixed_point_demo.py
#     python examples/data_services_programs.py
#     python examples/simple_agent_resource_model.py
#     python examples/diagram_export.py   # writes examples/exports/*.mmd
#
# - Read the original diagrams in the repository root `diagrams/` directory.
#
# - Explore the relationship to the papers (see README and VISION.md).
#
# The library is deliberately small at this stage so that the connection
# between the formal constructions and the Python objects remains transparent.
#
# Every diagram you can draw corresponds to a composition of the objects
# and morphisms you have just used.

# %% [markdown]
# ## 7. The diagrams layer — programmatic paper figures + Mermaid
#
# The `diagrams` submodule (and top-level re-exports) lets you build and
# render the exact constructions from the papers (and your own models)
# as `StringDiagram` trees or via the high-level `MermaidRenderer`.

# %%
from resource_diagrams.diagrams import MermaidRenderer, StringDiagram

renderer = MermaidRenderer()
print("Live fixed-point diagram (Paper I p.26):")
print(renderer.render_fixed_point_construction("succ")[:300] + "...\n")

# A tiny tree-built diagram
tiny = StringDiagram(
    diagrams.seq(  # type: ignore[attr-defined]
        diagrams.triangle("p", Object("Ξ")),  # type: ignore[attr-defined]
        diagrams.box("u", src=Object("Ξ"), tgt=Object("M")),  # type: ignore[attr-defined]
    ),
    title="tiny_evaluator",
)
print("Tiny programmatic diagram (to_mermaid head):")
print(tiny.to_mermaid()[:400] + "...")
print()

# %% [markdown]
# ## 8. The models layer — ReAct and resource idioms out of the box
#
# Higher-level builders compose everything into ready-to-analyze agent
# scaffolds with safety explanations already attached.

# %%
react_d = build_simple_react_diagram(["search"], cycles=1)
print("models.build_simple_react_diagram safety insight (excerpt):")
print(react_d.safety_explanation[:200] + "...")
print()
print("Its Mermaid (first 300 chars):")
print(react_d.to_mermaid()[:300] + "...")
print()

# %% [markdown]
# ## 9. Next Steps
#
# See the four examples/ scripts and the root `diagrams/*.mmd` for
# the canonical static references. The library now lets you move
# fluidly between executable models (MonoidalComputer), categorical
# primitives (Object/Morphism + DataService), diagrammatic construction,
# and domain-specific agent/resource patterns.

print("=" * 72)
print("Notebook script complete. All layers (core, diagrams, models) exercised.")
print("=" * 72)
