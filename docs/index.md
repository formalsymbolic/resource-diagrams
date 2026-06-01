# Resource Diagrams Documentation

Resource Diagrams provides string diagrams (grounded in monoidal category theory) for modeling resources, information flow, and structure in AI agent systems as an early experimental prototype / symbolic model.

The practical value demonstrated by the examples is making **policy and tool-definition copying (Δ forks on program triangles) versus one-way channels** visible in ReAct-style and tool-use scaffolds — as an aid to reviewing persistence and information-flow patterns that can be hard to see in text or ad-hoc drawings alone. All artifacts are illustrative; see the [README](../README.md) for scope and limitations.

For the primary documentation and quickstart, see the files in the repository root:

- [README.md](../README.md) — Overview, quickstart, audience callouts, and live examples.
- [ARCHITECTURE.md](../ARCHITECTURE.md) — Layered design (core categorical fidelity → diagrams → models) and non-goals.
- [VISION.md](../VISION.md) — Motivation, core hypothesis, and long-term ambition.
- [ROADMAP.md](../ROADMAP.md) — Current focus and future directions.

## Quick Audience Entry Points
- Researchers exploring diagrammatic methods: See the ReAct modeling pattern and fixed-point construction in `notebooks/reproducing_paper_i.py` and `examples/react_loop.py`.
- Agent builders and reviewers: Start with the ergonomic builders in `src/resource_diagrams/models/`. LangGraph users: see `docs/recipe_langgraph.md` and `examples/langgraph_style_transcription.py` for a zero-dependency transcription and review recipe.
- Formal methods researchers: The Paper I construction illustrations + `tests/paper_laws.py` structural correspondence checks (within the symbolic model).

The library source code is documented via standard Python docstrings. All golden-path examples and notebooks are single-command runnable from a fresh clone.

See [docs/gallery.md](gallery.md) for the curated visual gallery of the 01–09 diagram exports, including an "Interpreting the Diagrams (How to Use These)" section at the top and per-pattern notes on why the Δ/⊤ geometry is useful for the modeling use cases.

For detailed examples of modeling information flow in agent systems, see [diagrammatic-modeling-of-agent-information-flow.md](diagrammatic-modeling-of-agent-information-flow.md).