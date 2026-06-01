# Contributing to Resource Diagrams

Thank you for your interest in the project. Contributions are welcome.

## Ways to Contribute

- Bug reports and feature requests
- Improvements to the core library or diagram utilities
- New modeling patterns for AI/agent systems
- Better examples and documentation
- Feedback on what is (and isn't) useful in practice

## Development Setup

```bash
# Clone the repo
git clone https://github.com/resource-diagrams/resource-diagrams
cd resource-diagrams

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

We use:
- `ruff` for linting and formatting
- `mypy` (strict mode) for type checking
- `pytest` for tests

## Code Style

- Keep the core library small and focused.
- Prefer clarity over cleverness.
- When adding new modeling constructs, include at least one worked example.
- Public APIs should have clear docstrings.

## Documentation

If you're adding a significant new feature or modeling pattern, please add or update a notebook in `notebooks/` that demonstrates it.

## Questions

Feel free to open an issue for discussion before starting larger pieces of work.

Be respectful and constructive. This is a research-oriented project — good-faith technical disagreement is expected and welcome.
