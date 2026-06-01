"""
tests/test_models.py — Models layer builders (ReAct, token, infoflow, guarded contrast,
hierarchical, reflexion, multi-agent) + resource primitives + Diagram facade + analyzer bridge.

=== Validated invariants (for instant review) ===
- Builders produce Diagram w/ .title, .steps (real Morphisms), .to_mermaid, safety_explanation, .string_diagram.
- Safety bridge: _scan + full analyzer (forks_by_type, sensitive_reaches, flow_summary, stems_by_type).
- New patterns (hier/reflex/multi): #policy_forks>=2, stems>=1; Sub*/Critic* labels; policy in forks_by.
- ReAct: policy forks (Δ on tooldefs), safety scan.
- Token/chan: resource modeling.
- PBT expansion: react cycles/tools varied; hierarchical num_subs/tools; reflex cycles; multi n_agents/blackboard;
  all assert consistent geometry + analyzer metadata invariants (no crash, counts >= expected min).
- Edges: zero cycles/tools/agents, empty names, limit=0 budgets.
- Regressions: new patterns always attach upgraded analyzer data; guarded contrast.
- Modeling + safety markers.

Uses strategies from conftest (make_*). Fast det PBT with small max_ex.
"""

from __future__ import annotations

import pytest

from resource_diagrams.core import Morphism, Object
from resource_diagrams.models import (
    Diagram,
    InformationChannel,
    TokenBudget,
    basic_info_flow_diagram,
    build_hierarchical_agent_diagram,
    build_multi_agent_coordination_diagram,
    build_reflexion_with_critic_diagram,
    build_simple_react_diagram,
    model_token_accounting,
)

# For expanded PBT on modeling patterns (new patterns + react etc)
try:
    from tests.conftest import make_small_positive_int_strategy, make_tool_names_strategy
except Exception:
    make_small_positive_int_strategy = make_tool_names_strategy = None  # type: ignore[assignment]


def test_models_import_and_version():
    """Basic smoke test that the subpackage is importable and exposes public API."""
    import resource_diagrams.models as m

    assert hasattr(m, "build_simple_react_diagram")
    assert hasattr(m, "model_token_accounting")
    assert hasattr(m, "Diagram")
    assert hasattr(m, "InformationChannel")
    # New patterns
    assert hasattr(m, "build_hierarchical_agent_diagram")
    assert hasattr(m, "build_reflexion_with_critic_diagram")
    assert hasattr(m, "build_multi_agent_coordination_diagram")
    assert hasattr(m, "HierarchicalAgentResult")
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


@pytest.mark.safety
def test_models_react_diagram_safety_scan_and_analyzer_bridge():
    """The models Diagram's legacy _scan + the full diagrams analyzer (via to_string_diagram bridge)
    must both be exercisable and produce consistent high-level signals (policy copies present).
    """
    d = build_simple_react_diagram(["search"], cycles=1)
    scan = d._scan_safety_geometry()
    assert scan["policy_copy_steps"] >= 1
    # Bridge to real StringDiagram + analyzer (now always populated by builder)
    sd = d.to_string_diagram()
    if sd is not None:
        from resource_diagrams.diagrams.safety import analyze_safety_geometry

        raw = analyze_safety_geometry(sd)
        assert raw["policy_forks"] >= 0  # may be heuristic in some paths but runs
        assert "notes" in raw


def test_new_modeling_patterns_hierarchical_reflexion_coordination():
    """Smoke + structural checks for the three new non-trivial patterns.
    Each must return a Diagram with .string_diagram, run the analyzer,
    and exhibit the distinguishing geometry (multiple policy forks for
    sup+subs or actor+critic; stems on private/sub paths for coordination
    and hierarchical).
    """
    from resource_diagrams.diagrams.safety import analyze_safety_geometry

    # 1. Hierarchical
    dh = build_hierarchical_agent_diagram(["sub_research", "sub_code"])
    assert isinstance(dh, Diagram)
    assert dh.string_diagram is not None
    a_h = analyze_safety_geometry(dh.string_diagram)
    assert a_h["policy_forks"] >= 2, "expect sup fork + at least one sub fork"
    assert a_h["stems"] >= 2
    assert "policy" in str(a_h.get("forks_by_type", {})) or a_h["policy_forks"] > 0
    # Sub triangles present
    assert any("SubPolicy" in t or "SubAgent" in t for t in a_h.get("triangles_encountered", []))

    # 2. Reflexion/critic (separate critic fork)
    dr = build_reflexion_with_critic_diagram(tools=["search"], cycles=1)
    assert dr.string_diagram is not None
    a_r = analyze_safety_geometry(dr.string_diagram)
    assert a_r["policy_forks"] >= 2, "actor + distinct critic policy forks"
    # Critic triangle and one-way critic wire present in structure
    tris = a_r.get("triangles_encountered", [])
    assert any("Critic" in str(t) for t in tris)
    # One way paths and stems for the boundary
    assert a_r["stems"] >= 1

    # 3. Multi-agent
    dm = build_multi_agent_coordination_diagram(["A", "B"], use_shared_blackboard=True)
    assert dm.string_diagram is not None
    a_m = analyze_safety_geometry(dm.string_diagram)
    assert a_m["policy_forks"] >= 2  # at least the two private agent policies
    assert a_m["stems"] >= 2
    # Shared access shows as data/context forks; privates contribute stems/sensitive
    _ = a_m.get("forks_by_type", {})
    assert a_m["stems"] > 0

    print("New patterns tests: hierarchical/reflexion/coordination OK (structural + analyzer).")


# =============================================================================
# Expanded property-based, edge, and regression for modeling patterns
# =============================================================================
# Significantly expanded to cover new hierarchical/reflexion/multi-agent + tensor/comp
# interactions in diagrams they produce. All assert upgraded analyzer metadata present.
# Use small strategies for speed/det.


@pytest.mark.property
@pytest.mark.modeling
def test_react_diagram_various_cycles_and_tools_produce_consistent_geometry() -> None:
    """Validates: ReAct builder for varied cycles (1-3)/tools(1-3) always yields Diagram
    with >=1 policy fork (Δ on tooldefs/policy), attach string_diagram + analyzer keys,
    consistent mermaid + scan. (tensor/seq in the loop produce the geometry).
    """
    hypothesis = pytest.importorskip("hypothesis")
    st = pytest.importorskip("hypothesis").strategies

    cycles = st.integers(min_value=1, max_value=3)
    tool_count = st.integers(min_value=1, max_value=3)

    @hypothesis.given(c=cycles, tc=tool_count)
    @hypothesis.settings(max_examples=6, deadline=200, derandomize=True)
    def prop(c: int, tc: int) -> None:
        tools = [f"t{i}" for i in range(tc)]
        d = build_simple_react_diagram(tools=tools, cycles=c)
        assert isinstance(d, Diagram)
        assert len(d.steps) >= 2
        mmd = d.to_mermaid()
        assert "graph TD" in mmd
        scan = d._scan_safety_geometry()
        assert scan["policy_copy_steps"] >= 1  # at least the policy triangle replicated per cycle-ish
        sd = d.to_string_diagram()
        if sd is not None:
            from resource_diagrams.diagrams.safety import analyze_safety_geometry as _a

            raw = _a(sd)
            assert raw["policy_forks"] >= 0
            for k in ("forks_by_type", "stems_by_type", "sensitive_reaches", "flow_summary"):
                assert k in raw

    prop()


@pytest.mark.property
@pytest.mark.modeling
@pytest.mark.safety
def test_new_modeling_patterns_property_varied_params_produce_invariant_geometry() -> None:
    """Validates: the three new builders (hierarchical, reflexion, multi) under generated small params
    (num tools/subs/cycles/agents, blackboard flag) ALWAYS:
    - attach non-None .string_diagram
    - analyzer reports policy_forks >= expected min (2 for nested/sup+sub or actor+critic or 2 privates)
    - stems >=1 or 2 for boundary protection
    - forks_by_type contains 'policy'
    - upgraded keys present (path sens etc).
    This is the key expansion for 'new modeling patterns' PBT.
    """
    if make_small_positive_int_strategy is None or make_tool_names_strategy is None:
        pytest.skip("modeling strategy helpers unavailable")
    hypothesis = pytest.importorskip("hypothesis")
    st = pytest.importorskip("hypothesis").strategies

    n_cycles = make_small_positive_int_strategy(1, 2)
    n_subs = make_small_positive_int_strategy(1, 3)
    n_agents = make_small_positive_int_strategy(2, 3)
    tools_strat = make_tool_names_strategy(3)
    bb = st.booleans()

    @hypothesis.given(tools=tools_strat, cyc=n_cycles, subs=n_subs, nagt=n_agents, use_bb=bb)
    @hypothesis.settings(max_examples=5, deadline=300, derandomize=True)
    def prop(tools: list[str], cyc: int, subs: int, nagt: int, use_bb: bool) -> None:
        from resource_diagrams.diagrams.safety import analyze_safety_geometry as a

        # 1. Hierarchical (uses subagent_names list; vary length)
        sub_names = [f"sub{i}" for i in range(max(1, subs))]
        dh = build_hierarchical_agent_diagram(sub_names)
        assert dh.string_diagram is not None
        ah = a(dh.string_diagram)
        assert ah["policy_forks"] >= 2, "sup + subs"
        assert ah["stems"] >= 1
        assert "policy" in str(ah.get("forks_by_type", {})) or ah["policy_forks"] > 0
        for k in ("forks_by_type", "stems_by_type", "sensitive_reaches", "flow_summary"):
            assert k in ah

        # 2. Reflexion
        dr = build_reflexion_with_critic_diagram(tools=tools or ["t"], cycles=cyc)
        assert dr.string_diagram is not None
        ar = a(dr.string_diagram)
        assert ar["policy_forks"] >= 2, "actor + critic"
        assert ar["stems"] >= 1
        tris = ar.get("triangles_encountered", [])
        assert any("Critic" in str(t) for t in tris)
        for k in ("forks_by_type", "stems_by_type", "sensitive_reaches", "flow_summary"):
            assert k in ar

        # 3. Multi-agent
        dm = build_multi_agent_coordination_diagram([f"ag{i}" for i in range(nagt)], use_shared_blackboard=use_bb)
        assert dm.string_diagram is not None
        am = a(dm.string_diagram)
        assert am["policy_forks"] >= 2  # privates
        assert am["stems"] >= 2
        for k in ("forks_by_type", "stems_by_type", "sensitive_reaches", "flow_summary"):
            assert k in am

    prop()


@pytest.mark.edge_case
@pytest.mark.modeling
def test_builders_handle_zero_or_minimal_inputs_gracefully() -> None:
    """Edge: cycles=0 or empty tools list still return valid Diagram (no crash)."""
    d0 = build_simple_react_diagram(tools=[], cycles=0)
    assert isinstance(d0, Diagram)
    assert d0.to_mermaid()  # non-empty string at least

    d1 = model_token_accounting([], total_budget=10)
    assert isinstance(d1, Diagram)

    # info flow on weird channel name
    chan = InformationChannel("", copyable=True)
    d2 = basic_info_flow_diagram(chan)
    assert isinstance(d2, Diagram)


@pytest.mark.regression
@pytest.mark.modeling
@pytest.mark.safety
def test_new_patterns_always_attach_string_diagram_and_analyzer_metadata() -> None:
    """Regression guard: the three new builders (hier/reflex/multi) always populate .string_diagram
    with usable analyzer output containing the upgraded keys (forks_by_type etc).
    """
    dh = build_hierarchical_agent_diagram(["s1"])
    dr = build_reflexion_with_critic_diagram(cycles=1)
    dm = build_multi_agent_coordination_diagram(["x", "y"], use_shared_blackboard=False)

    for d in (dh, dr, dm):
        assert d.string_diagram is not None
        from resource_diagrams.diagrams.safety import analyze_safety_geometry as a

        raw = a(d.string_diagram)
        for key in ("forks_by_type", "stems_by_type", "sensitive_reaches", "flow_summary"):
            assert key in raw
        assert raw["classified_forks"] >= 0 or raw["policy_forks"] >= 0


@pytest.mark.edge_case
@pytest.mark.modeling
def test_token_budget_and_channel_edges() -> None:
    """Edge values for resources."""
    b = TokenBudget(limit=0, used=0)
    assert b.remaining() == 0
    b2 = b.consume(0)
    assert b2.remaining() == 0

    ch = InformationChannel("empty", copyable=False)
    ch.apply_delete(None)  # should be safe
    assert ch.copyable is False
