# Governance (Lightweight)

Resource Diagrams is a research-oriented open source project.

## Scope
We maintain a narrow, well-scoped focus on diagrammatic methods grounded in the Monoidal Computer papers for modeling resources and information flow in computational (especially AI/agent) systems. See `ARCHITECTURE.md` (Non-Goals) and `ROADMAP.md` for explicit boundaries.

## Decision Making
- Technical direction and scope enforcement are guided by the principles in `ARCHITECTURE.md` and `VISION.md`.
- Changes that would expand scope beyond the stated non-goals require clear justification and discussion.
- Structural correspondence to the cited papers' diagrammatic constructions (especially Paper I) is valued. Contributions that strengthen the clarity and test coverage of these correspondences (e.g., via `tests/paper_laws.py`) are welcome.

## Contributions
We welcome contributions from researchers and engineers in AI safety, formal methods, categorical semantics, and oversight. See `CONTRIBUTING.md` for practical guidance.

We particularly encourage:
- New modeling patterns that make safety-relevant geometry (Δ vs. ⊤) more visible and structural.
- Improvements to diagram rendering and export quality for academic use.
- Strengthening of structural checks against the source diagrammatic constructions.

## Review Process
Pull requests are reviewed for:
- Correctness and clear correspondence to the source formal/diagrammatic foundations (within the documented scope of the symbolic model)
- Adherence to non-goals
- Quality of documentation and examples
- Test coverage (especially for new modeling constructs)

Good-faith technical disagreement is expected and welcome.

## Contact
For governance or scope questions, open an issue or use the contacts in `SECURITY.md`.