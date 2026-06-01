# Architecture & Design Principles

This document describes how Resource Diagrams is structured and the principles that guide its design.

## Guiding Principles

1. **Diagrams as the primary interface**
   - The value of this project comes from making computational structure *visible* and *manipulable* in string diagram form.
   - Code should be written so that the diagrammatic representation arises naturally from the underlying structure.

2. **Formal foundations, practical ergonomics**
   - The design remains faithful to the core ideas from the Monoidal Computer papers — specifically the Paper I foundation (data services as comonoids, universal and partial evaluators, diagrammatic fixed-point construction) together with practical modeling idioms for AI safety (ReAct, resources, information flow).
   - Ideas from later papers (grading/normal complexity from Paper II; coalgebraic views from Paper III) are aspirational and tracked in ROADMAP.md; they are not part of the delivered Phase 1 scope.
   - Usability for working researchers is prioritized alongside fidelity to the formal foundations.

3. **Layered architecture**
   - Keep the categorical core small, pure, and well-specified.
   - Build higher-level, domain-specific modeling layers on top (especially for AI/agent systems).
   - LLM-assisted or external-model features are future work (no optional extras shipped in v0.1; core remains fully self-contained).

4. **Self-contained by default**
   - The core library (Phase 1) is fully usable with no network access and no dependencies beyond Python stdlib.
   - Any future features requiring external models (e.g. LLM assistance) will live behind optional extras and are explicitly not part of the current delivered scope.

5. **Security and auditability mindset**
   - The project exists to help analyze security-relevant properties of AI systems.
   - The design emphasizes representations that are inspectable, explainable, and, where possible, auditable.

## Layered Structure (Current Reality — Phase 1)

**Current implementation scope**: faithful realization of the Paper I core (data services, universal and partial evaluators, diagrammatic fixed-point construction) together with practical AI safety modeling idioms (ReAct, resources, information flow).

```
src/resource_diagrams/
├── core.py                  # Basic categorical primitives (Object, Morphism, composition, tensor, program_code)
├── data_services.py         # Copy (Δ), delete (⊤) — the "classical data" layer (Paper I §3)
├── evaluators.py            # Universal + partial evaluators + diagrammatic fixed-point (Paper I §4, §6)
├── diagrams/                # String diagram construction + high-quality MermaidRenderer (reproduces paper figures 01-04 + general trees)
│   ├── diagram.py
│   ├── mermaid_renderer.py
│   └── ...
└── models/                  # Higher-level, example-driven idioms for AI/agent systems (the "why it matters" layer)
    ├── agents.py            # ReAct-style scaffolds with explicit policy/tool copies vs one-way flows
    ├── reasoning.py         # Reasoning traces, info-flow diagrams
    └── resources.py         # Token budgets, information channels, one-way transforms
```

**Notes**:
- The implementation uses flat modules (not nested `core/` packages) for simplicity in v0.1.
- `grading/` (Paper II) and `augmentation/` (LLM features) do **not** exist yet; they are explicitly future work (see ROADMAP.md).
- The previous `openai` optional extra has been removed (dead code; no implementation or imports anywhere).
- All documentation lives in the package root (`README.md`, this file, `ROADMAP.md`, `VISION.md`) alongside the code. The `docs/` subdirectory is currently empty.

### Core Layer (`core.py`, `data_services.py`, `evaluators.py`)
Contains the faithful implementation of the Paper I structures. This layer is relatively stable and well-documented with references back to the source material (Def 4.1, Lemma 6.2, Prop 6.1, §3 comonoids).

### Modeling Layer (`models/`)
This layer develops representations for common AI constructs (ReAct loops, resource accounting, information flow) as diagrams. It is expected to evolve as useful modeling patterns are identified. It builds on the core layer while remaining independent of external services.

**Diagram layer (post unification)**: The high-level builders in `models/` now construct and consume real `diagrams.StringDiagram` trees (using `fork`/`stem`/`triangle` etc. for explicit Δ/⊤ geometry on policy vs one-way channels). Rendering delegates to `MermaidRenderer`. `models.Diagram` acts as a thin ergonomic facade for compatibility. The diagrams layer is the single source of truth; safety properties are structural in the diagram tree.

### Future Layers (Not Yet Present)
- Grading / complexity (Paper II concepts) — aspirational.
- Augmentation / LLM-assisted diagram tools — future, would require optional extra if implemented.

## Key Design Decisions

- **Mermaid as the primary export format** for now (ubiquitous, good enough for most purposes).
- **Programs as data** is a first-class concept (this is one of the most powerful ideas from the original work).
- Resources are modeled explicitly where possible (tokens, steps, information, tool calls, etc.).
- The library does not aim to provide a full agent framework or execution engine.

## Non-Goals (by design)

- The project is not a general-purpose diagramming tool.
- Machine-checked proofs in a proof assistant are not a current objective.
- The library is not intended to compete with existing agent or evaluation frameworks.
- Automatic diagram synthesis from arbitrary code is out of scope for the initial versions.

This architecture is intended to be simple enough to understand quickly while still providing a solid foundation for serious exploration of diagrammatic methods in AI safety.

**Current scope**: The library provides a faithful implementation of the Paper I core together with practical safety modeling idioms. The design focuses on the foundational categorical structures from the source papers alongside usable modeling patterns for AI systems.
