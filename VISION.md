# Vision

Resource Diagrams is an experimental project exploring whether ideas from string diagrams and monoidal categories can be turned into small, useful visualization and counting tools for reasoning about copying, deletion, and information flow in agent-like systems.

## The Core Hypothesis

Many of the most important properties of AI systems (especially agentic and scaffolded systems) are fundamentally about **resources**:
- Information flow and leakage
- Computational steps and token usage
- The difficulty of certain transformations (e.g. "how hard is it for this system to produce harmful behavior?")
- The structure of control flow and state

Current tools for analyzing these properties are mostly textual, informal, or low-level. String diagrams offer a potential middle ground: sufficiently visual to support human intuition while remaining structured enough to support clear compositional reasoning (in the illustrative models).

## Why This Might Matter

As agentic systems become more common, having better ways to visualize and count distinctions such as "this piece of policy gets copied everywhere" vs. "this user observation should only be used once" could be useful for review and reasoning.

This project is a small experiment in that direction. It is not claimed to be a security tool or a replacement for existing analysis methods.

## Approach

The library implements key ideas from the Monoidal Computer framework (Pavlovic et al.) and develops practical idioms for applying them to real AI systems.

**Current implementation**: illustrative realization (symbolic model) of the Paper I core ideas (data services as comonoids, universal and partial evaluators per Def 4.1, diagrammatic fixed-point construction per Lemma 6.2 / Prop 6.1 style) together with practical AI safety modeling idioms (ReAct scaffolds highlighting policy copy asymmetries, explicit resource and token accounting, information flow and leakage channels).

The project prioritizes:
- Fidelity (where claimed) to the underlying formal ideas (Paper I first), with explicit scoping as illustrative models
- Usability for working researchers and engineers
- Remaining usable without external services for core functionality

Later papers (Paper II grading / normal complexity; Paper III coalgebraic views) inform the vision and some modeling primitives (e.g. TokenBudget) but full support is future work (see ROADMAP.md).

## Scope and Philosophy

This is not an attempt to replace existing tools, nor is it primarily about automatic diagram generation from code. It is an exploration of a different *lens* — one that treats programs, processes, and resources as first-class objects that can be composed, transformed, and inspected visually.

The most valuable contributions are expected to come from developing clear, useful ways to model important AI constructs (tool use, reasoning traces, memory, planning, etc.) as diagrams, and from identifying which security and safety properties become more legible in this representation.

## Current Intent

The immediate goal is to produce a small number of clear, runnable examples that make certain diagrammatic distinctions legible, and to see whether this style of modeling is useful to anyone working on agent systems or their oversight.

It is an early, exploratory artifact. Substantial further work would be required before it could be considered a reliable tool for high-stakes analysis.
