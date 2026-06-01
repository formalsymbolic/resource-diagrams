#!/usr/bin/env python3
"""
examples/resource_trace.py

Standalone runnable example of explicit resource (token) accounting
as a first-class wire in a diagram.

Uses model_token_accounting from the models layer. Demonstrates how
budget depletion becomes a structural, inspectable feature rather
than hidden in logs or code.

Run:
    python examples/resource_trace.py

(Direct execution from fresh clone supported via consistent guard.)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Consistent minimal bootstrap (sys.path guard) across examples.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams.models import TokenBudget, model_token_accounting


def main() -> None:
    print("=" * 72)
    print("RESOURCE DIAGRAMS — Token Accounting Example")
    print("Core modeling pattern: Resource usage (tokens, compute steps) as diagrams")
    print("=" * 72)
    print()

    # A realistic-ish agent trace cost profile
    trace = [
        ("reason", 38),
        ("tool_call:web_search", 145),
        ("observe", 22),
        ("reason", 51),
        ("tool_call:calculator", 67),
        ("observe", 19),
        ("final_answer", 12),
    ]

    budget = TokenBudget(limit=512, used=0)
    print(f"Starting with {budget}")

    d = model_token_accounting(trace, total_budget=512, title="Agent Trace Token Accounting")

    print("Diagram constructed with parallel TokenBudget wire.")
    print("Cumulative modeled spend:", sum(c for _, c in trace))
    print()

    print("--- Mermaid source ---")
    print()
    print(d.to_mermaid())
    print()

    print("--- Safety / Oversight Insight ---")
    print()
    print(
        "Illustrative (the diagram + token annotations make it obvious where "
        "the bulk of the budget was spent). When combined with ReAct (Δ policy "
        "copies visible via annotations), an analyst can inspect whether copied "
        "sub-policy could drive expensive calls before budget exhaustion. "
        "(See model safety_explanation for the labeled interpretation.)"
    )
    print()

    print("Direct TokenBudget object (can be passed to other builders):")
    print(repr(budget.consume(100)))
    print()

    print("=" * 72)
    print("resource_trace.py complete. Resources are now first-class wires.")
    print("=" * 72)


if __name__ == "__main__":
    main()
