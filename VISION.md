# Vision

Resource Diagrams exists to explore whether the graphical language of string diagrams — grounded in the formal framework of monoidal categories — can become a practical and powerful tool for understanding and securing advanced AI systems.

## The Core Hypothesis

Many of the most important properties of AI systems (especially agentic and scaffolded systems) are fundamentally about **resources**:
- Information flow and leakage
- Computational steps and token usage
- The difficulty of certain transformations (e.g. "how hard is it for this system to produce harmful behavior?")
- The structure of control flow and state

Current tools for analyzing these properties are mostly textual, informal, or low-level. String diagrams offer a potential middle ground: sufficiently visual to support human intuition while remaining formal enough to support rigorous reasoning.

## Why This Matters

As AI systems become more capable and more agentic, the ability to clearly represent and analyze their structure becomes increasingly important for:
- Security analysis and red-teaming
- Oversight and evaluation
- Understanding emergent behaviors
- Building more reliable and interpretable systems

Particular attention is given to techniques that can help make the "resource" aspects of these systems more legible, drawing inspiration from earlier work on computational resources as security primitives.

## Approach

The library implements key ideas from the Monoidal Computer framework (Pavlovic et al.) and develops practical idioms for applying them to real AI systems.

**Current implementation**: faithful realization of the Paper I core (data services as comonoids, universal and partial evaluators per Def 4.1, diagrammatic fixed-point construction per Lemma 6.2 / Prop 6.1) together with practical AI safety modeling idioms (ReAct scaffolds highlighting policy copy asymmetries, explicit resource and token accounting, information flow and leakage channels).

The project prioritizes:
- Faithfulness to the underlying formal ideas (Paper I first)
- Usability for working researchers and engineers
- Remaining usable without external services for core functionality

Later papers (Paper II grading / normal complexity; Paper III coalgebraic views) inform the vision and some modeling primitives (e.g. TokenBudget) but full support is future work (see ROADMAP.md).

## Scope and Philosophy

This is not an attempt to replace existing tools, nor is it primarily about automatic diagram generation from code. It is an exploration of a different *lens* — one that treats programs, processes, and resources as first-class objects that can be composed, transformed, and inspected visually.

The most valuable contributions are expected to come from developing clear, useful ways to model important AI constructs (tool use, reasoning traces, memory, planning, etc.) as diagrams, and from identifying which security and safety properties become more legible in this representation.

## Long-term Ambition

If successful, this line of work could contribute to a richer set of conceptual and practical tools for anyone who needs to understand what complex AI systems are actually doing — particularly when those systems are being used in high-stakes or security-sensitive contexts.

The project is a research effort to develop and evaluate diagrammatic methods for the analysis of computational systems.
