# Changelog

All notable changes to Resource Diagrams will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial public release of the core library.
- Faithful implementation of the fixed-point construction from Monoidal Computer Paper I (Lemma 6.2 and Proposition 6.1).
- String diagram construction and rendering layer with support for the canonical figures from the source papers.
- Higher-level modeling idioms for ReAct-style scaffolds, resource accounting, and information-flow analysis.
- Runnable examples and literate notebooks demonstrating both the formal constructions and their application to AI system modeling.
- Dependabot configuration for automated dependency and GitHub Actions updates.
- Expanded issue templates and pull request template for better contributor workflow.
- `analyze_safety_geometry` structural analyzer (in diagrams.safety) for machine-readable Δ vs one-way insights.
- `examples/reflexion_loop.py` extending the core policy-copying security surface pattern.
- New applied pattern `build_guarded_vs_unguarded_contrast` (and `GuardedContrast` result) that makes the security effect of inserting an explicit Stem (⊤) on a one-way sensitive channel directly visible and quantifiable by the analyzer.
- `examples/guarded_contrast.py` — self-contained demonstration of the guarded contrast with side-by-side analyzer output.
- `examples/langgraph_style_transcription.py` + `docs/recipe_langgraph.md` — zero-dependency transcription recipe and runnable example for LangGraph StateGraph patterns.
- `generate_security_report`, `SecurityReport`, and `SecurityFinding` — structured analysis of copying and termination structure in diagrams (in addition to the existing lower-level `analyze_safety_geometry`).
- New document on diagrammatic modeling of agent information flow (now at `docs/diagrammatic-modeling-of-agent-information-flow.md`).
- Refinements to README and project description for clarity and consistency of tone.
- Richer structural `StringDiagram` construction inside `build_simple_react_diagram`.
- Updated gallery, docs index, and cross-references.

### Changed
- Improved consistency between models layer and core diagrams primitives in key builders (richer structural StringDiagram support in ReAct builder).
- Removed heavy-weight external Code of Conduct in favor of lightweight project expectations (see CONTRIBUTING.md).

## [0.1.0] - 2026-06-01

### Added
- Core categorical primitives (`Object`, `Morphism`, `DataService`, `MonoidalComputer`).
- Diagrams layer with `StringDiagram` and `MermaidRenderer`.
- Models layer providing ergonomic builders for common AI/agent constructs.
- Comprehensive test suite with structural verification of paper laws (including `paper_laws.py`).
- Full documentation suite (README, ARCHITECTURE, VISION, ROADMAP, SECURITY, DEVELOPMENT, CONTRIBUTING, GOVERNANCE).
- `CITATION.cff` for academic citation support.
- `CHANGELOG.md` following Keep a Changelog format.
- Bootstrap guards in all examples and notebooks for zero-friction execution from fresh clone.
- Professional GitHub scaffolding (CI workflow with packaging hygiene checks, basic issue templates).

### Fixed
- Various documentation inconsistencies and scope alignment issues identified during pre-release review.

## [0.0.3] - 2026-05-20

### Added
- Initial structural diagram support in models layer (early unification work).
- `GOVERNANCE.md` and expanded contributor guidelines.
- Additional paper figure exports and improved `diagram_export.py`.

### Changed
- Refactored legacy ad-hoc diagram construction toward real `StringDiagram` usage in flagship builders.

## [0.0.2] - 2026-05-05

### Added
- Core evaluators and data services implementation with protocol-based extensibility.
- First set of runnable examples demonstrating fixed-point construction and basic ReAct modeling.
- Strict mypy + ruff configuration and CI integration.

## [0.0.1] - 2026-04-15

### Added
- Initial project scaffolding and core monoidal types (`Object`, `Morphism`).
- Basic diagram rendering (Mermaid output).
- Foundational tests for data service laws.