"""Tests for the models subpackage (construction + diagram structure invariants)."""

from __future__ import annotations

import pytest

from resource_diagrams.core import Morphism, Object
from resource_diagrams.models import (
    Diagram,
    InformationChannel,
    TokenBudget,
    basic_info_flow_diagram,
    build_simple_react_diagram,
    model_token_accounting,
)


def test_models_import_and_version():
    """Basic smoke test that the subpackage is importable and exposes public API."""
    import resource_diagrams.models as m

    assert hasattr(m, "build_simple_react_diagram")
    assert hasattr(m, "model_token_accounting")
    assert hasattr(m, "Diagram")
    assert hasattr(m, "InformationChannel")
    assert m.__version__.startswith("0.1")


def test_react_diagram_construction():
    """build_simple_react_diagram produces a Diagram with expected structure."""
    d = build_simple_react_diagram(tools=["search", "calc"], cycles=1)

    assert isinstance(d, Diagram)
    assert "ReAct" in d.title or "react" in d.title.lower()
    assert len(d.steps) >= 3  # reason + at least one tool + observe
    assert any("Reason" in str(s) for s in d.steps)
    assert any("ToolCall" in str(s) for s in d.steps)

    mmd = d.to_mermaid()
    assert "graph TD" in mmd
    assert "▼" in mmd or "policy" in mmd.lower()  # program triangle
    # Safety note about Δ vs one-way must be present (the key insight)
    assert "Δ" in mmd or "copied policy" in mmd.lower() or "one way" in mmd.lower()

    # Safety text is explicitly labeled as illustrative and backed by the scanner
    assert d.safety_explanation.startswith("Illustrative interpretation")
    expl = d.get_safety_explanation()
    assert "Illustrative interpretation" in expl
    scan = d._scan_safety_geometry()
    assert "policy_copy_steps" in scan and isinstance(scan["policy_copy_steps"], int)


def test_token_accounting_diagram():
    """model_token_accounting produces resource-annotated diagram."""
    trace = [("reason", 10), ("tool", 50), ("final", 5)]
    d = model_token_accounting(trace, total_budget=100)

    assert isinstance(d, Diagram)
    assert "Token" in d.title or "token" in d.title.lower()
    mmd = d.to_mermaid()
    assert "TokenBudget" in mmd or "tokens" in mmd.lower()
    assert "100" in mmd or "budget" in mmd.lower()  # budget mention


def test_info_flow_diagram_and_channels():
    """basic_info_flow_diagram and InformationChannel surface copy/delete."""
    chan = InformationChannel("test_chan", copyable=True)
    assert chan.copyable is True

    d = basic_info_flow_diagram(chan)
    assert isinstance(d, Diagram)
    mmd = d.to_mermaid()
    assert "Δ" in mmd or "copyable" in mmd.lower() or "leak" in mmd.lower()

    # One-way channel
    oneway = InformationChannel("secret", copyable=False)
    assert oneway.copyable is False
    # apply_delete should not raise
    oneway.apply_delete("value")


def test_diagram_to_string_diagram_integration():
    """The models Diagram can produce a diagrams.StringDiagram (when possible)."""
    d = build_simple_react_diagram(["t"], cycles=1)
    sd = d.to_string_diagram()
    # May be None in some edge cases, but when present must be usable
    if sd is not None:
        from resource_diagrams.diagrams import StringDiagram

        assert isinstance(sd, StringDiagram)
        assert sd.title == d.title
        # official renderer should succeed
        mmd2 = sd.to_mermaid()
        assert len(mmd2) > 50
        # bridge now attaches safety metadata when possible (best effort)
        meta = getattr(sd, "metadata", {}) or {}
        if meta:
            assert "models_safety_explanation" in meta or "safety" in str(meta).lower()


def test_underlying_morphisms_are_real_core_objects():
    """The .steps in a models diagram are genuine core.Morphism instances."""
    d = build_simple_react_diagram(["x"], cycles=1)
    for step in d.steps:
        assert isinstance(step, Morphism)
        assert isinstance(step.src, Object)
        assert callable(step.impl)


def test_token_budget_model():
    b = TokenBudget(limit=200, used=30)
    assert b.remaining() == 170
    b2 = b.consume(50)
    assert b2.remaining() == 120
    assert "TokenBudget" in repr(b2)
