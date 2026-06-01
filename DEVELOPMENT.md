# Development

This document explains how to set up the project for local development.

## Setup

```bash
# Clone the repository
git clone https://github.com/resource-diagrams/resource-diagrams.git
cd resource-diagrams

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install the package in editable mode with development dependencies
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## Type Checking

```bash
mypy src
```

## Linting and Formatting

```bash
ruff check .
ruff format .
```

## Running Examples / Notebooks

All 8 scripts under `examples/` and both notebooks (jupytext-style .py with # %% cells) are designed to be run directly with a **single command** from the `resource-diagrams/` checkout directory:

```bash
python examples/fixed_point_demo.py
python examples/react_loop.py
python examples/diagram_export.py   # regenerates exactly 01-04 paper .mmd
python examples/simple_agent_resource_model.py
# ... all others (data_services_programs.py, info_flow_diagram.py, resource_trace.py, diagram_export.py)
python notebooks/getting_started.py
python notebooks/reproducing_paper_i.py  # main reproduction + modeling demonstration
```

- **Fresh clone (no install, no PYTHONPATH)**: Works out of the box. Every file includes a minimal consistent `sys.path` guard (see e.g. top of any example) that adds `src/` before the first `from resource_diagrams` import.
- **After editable install** (recommended for development): The guards are harmless; `from resource_diagrams...` resolves via the installed editable package.
- Notebooks: Run as plain Python (they print + execute top-to-bottom) or convert with `pip install jupytext && jupytext --to ipynb notebooks/01_*.py` then open in Jupyter/VS Code. The # %% delimiters make them first-class notebooks.
- All commands assume you are inside the `resource-diagrams/` directory (the package root for paths in guards/docs).

See also the "Installation" and "Usage" sections of `README.md` (which now prioritize direct-run + editable paths for the unpublished state).

## Project Structure

- `src/resource_diagrams/` — The actual library code
- `tests/` — Test suite
- `notebooks/` — Exploratory and example notebooks
- `examples/` — Standalone example scripts

## Contribution Workflow

1. Create a feature branch.
2. Make your changes.
3. Ensure tests pass and type checking is clean.
4. Open a pull request.

We use strict type checking and formatting. Please run the linting and type commands before submitting a PR.

## Questions

Open an issue for discussion on larger changes or design questions.
