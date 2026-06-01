# Resource Diagrams Documentation

Resource Diagrams provides string diagrams (grounded in monoidal category theory) for modeling resources, information flow, and security-relevant structure in AI agent systems.

The strongest practical value is making **policy and tool-definition copying (Δ forks on program triangles) versus one-way channels** visible in ReAct-style and tool-use scaffolds — surfacing persistence and leakage surfaces that are hard to see in text or ad-hoc drawings.

For the primary documentation and quickstart, see the files in the repository root:

- [README.md](../README.md) — Overview, quickstart, audience callouts, and live examples.
- [ARCHITECTURE.md](../ARCHITECTURE.md) — Layered design (core categorical fidelity → diagrams → models) and non-goals.
- [VISION.md](../VISION.md) — Motivation, core hypothesis, and long-term ambition.
- [ROADMAP.md](../ROADMAP.md) — Current focus and future directions.

## Quick Audience Entry Points
- AI safety & oversight researchers: See the ReAct security surface pattern in `notebooks/reproducing_paper_i.py` and `examples/react_loop.py`.
- Agent builders: Start with the ergonomic builders in `src/resource_diagrams/models/`. LangGraph users: see `docs/recipe_langgraph.md` and `examples/langgraph_style_transcription.py` for a zero-dependency transcription and review recipe.
- Formal methods researchers: The faithful Paper I implementation + `tests/paper_laws.py` structural verification.

The library source code is documented via standard Python docstrings. All golden-path examples and notebooks are single-command runnable from a fresh clone.

See [docs/gallery.md](gallery.md) for the best current diagrams illustrating the core value.

For detailed examples of modeling information flow in agent systems, see [diagrammatic-modeling-of-agent-information-flow.md](diagrammatic-modeling-of-agent-information-flow.md).