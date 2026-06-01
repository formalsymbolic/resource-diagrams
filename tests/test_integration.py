"""
tests/test_integration.py — Integration, roundtrip, smoke, and modeling tests.

Covers cross-layer interactions:
- Core (Object/Morphism enhancements) + diagrams (builders, StringDiagram, to_*)
- MonoidalComputer + DataService + diagrams (paper figure reproduction)
- Models layer (direct submodule imports for isolation + top-level; now-complete with reasoning.Diagram)
- Construction of diagrams from modeled agent steps (Morphism.program_code + to_diagram)
- MermaidRenderer specialized paper renderers (high-signal for formal fidelity)
- Resource / agent idioms (InformationChannel Δ/⊤, TokenBudget, ToolCall etc.)

Uses paper_laws helpers. Every new public API (post-parallel-work) has smoke coverage.
Fast, deterministic. Models layer (now complete with reasoning.Diagram) exercised
both via submodule aliases and (in test_models.py) top-level package imports.
Core + diagrams + evaluators fidelity tests are not blocked by any gaps.
"""

import tempfile
from pathlib import Path

import pytest

from resource_diagrams import DataService, MonoidalComputer, Morphism, Object
from resource_diagrams.core import XI, I
from resource_diagrams.diagrams import (
    Box,
    Fork,
    MermaidRenderer,
    StringDiagram,
    Tensor,
    Triangle,
    Wire,
    box,
    fork,
    from_morphism,
    seq,
    stem,
    tensor,
    triangle,
    wire,
)

# Direct submodule imports (agents/resources) for test isolation.
# (Top-level `from resource_diagrams.models import ...` now also works since
# reasoning.py + Diagram landed; these submodules avoid re-export side effects.)
from resource_diagrams.models import agents as models_agents
from resource_diagrams.models import resources as models_resources

from .paper_laws import (
    assert_diagram_reproduces_paper_figure,
    assert_morphism_roundtrip_via_diagram,
)


# =============================================================================
# Core + Diagrams integration (new Object/Morphism operators + to_diagram)
# =============================================================================

def test_object_tensor_and_matmul_and_canonicals() -> None:
    """New monoidal structure on Object (Paper I Fig 3 + unit laws)."""
    a, b = Object("A"), Object("B")
    assert (a @ b).name == "(A ⊗ B)"
    assert (a.tensor(b)).name == "(A ⊗ B)"
    assert XI @ I == XI  # unitors
    assert I.tensor(N := Object("N")) == N
    assert XI.is_unit is False
    assert I.is_unit is True


def test_morphism_composition_rshift_and_tensor_and_call() -> None:
    """New composition operators on Morphism (>> , @ , __call__)."""
    A, B, C = Object("A"), Object("B"), Object("C")

    def f(x):
        return ("f", x)

    def g(y):
        return ("g", y)

    m1 = Morphism("f", A, B, impl=f, program_code="f_code")
    m2 = Morphism("g", B, C, impl=g, program_code="g_code")

    composed = m1 >> m2
    assert composed.name == "(f;g)"
    assert composed.src == A and composed.tgt == C
    assert composed.program_code == "(f_code;g_code)"
    assert composed("input") == ("g", ("f", "input"))

    # Tensor
    t = m1 @ m2
    assert "⊗" in t.name
    assert t( (1, 2) ) == ( ("f", 1), ("g", 2) )

    # __call__
    assert m1("x") == ("f", "x")


def test_morphism_pure_and_program_factories_and_to_diagram_roundtrip() -> None:
    """Factories + to_diagram integration (new on Morphism)."""
    A, B = Object("A"), Object("B")

    def impl(x):
        return x

    pure = Morphism.pure("pure_f", A, B, impl)
    assert pure.program_code is None

    prog = Morphism.program("prog_f", A, B, "my_code_42", impl)
    assert prog.program_code == "my_code_42"
    assert DataService.is_basic_data(prog.program_code)

    # Roundtrip to diagram + data service copy on the code
    d = prog.to_diagram()
    assert isinstance(d, StringDiagram)
    assert_morphism_roundtrip_via_diagram(prog)


# =============================================================================
# Diagrams layer smoke + paper figure reproduction
# =============================================================================

def test_all_diagram_builders_and_elements_construct_and_repr() -> None:
    """Smoke every exported builder + element class (diagrams/ layer)."""
    xi = XI
    w = wire(xi)
    assert isinstance(w, Wire)
    b = box("u", src=xi, tgt=Object("M"))
    assert isinstance(b, Box)
    t = triangle("p42", xi)
    assert isinstance(t, Triangle)
    f = fork(xi)
    assert isinstance(f, Fork)
    s = stem(xi)
    assert "Stem" in repr(s)

    # Composites
    seq_comp = seq(t, b)
    ten = tensor(w, f)
    assert isinstance(seq_comp, type(seq(w, b)))  # Sequential
    assert isinstance(ten, Tensor)


def test_string_diagram_validate_to_text_to_mermaid_and_save(tmp_path: Path) -> None:
    """StringDiagram core methods + persistence (save_mmd uses tmp)."""
    xi = XI
    d = StringDiagram(
        seq( triangle("policy", xi), box("reason", src=xi, tgt=xi) ),
        title="integration_test_agent_step",
        metadata={"paper": "Def 4.1"},
    )
    assert d.validate() or "arity_warning" in d.metadata, "heuristic validate should pass or note warning"
    text = d.to_text()
    assert "▼ policy" in text
    mmd = d.to_mermaid()
    assert "graph TD" in mmd or "%%" in mmd  # Mermaid output marker

    # save
    out = tmp_path / "test_save.mmd"
    d.save_mmd(out)
    assert out.exists()
    assert "agent_step" in out.read_text()


def test_mermaid_renderer_specialized_paper_renders_contain_canonical_content() -> None:
    """The dedicated render_* methods must reproduce paper figures (highest credibility)."""
    r = MermaidRenderer()

    basic = r.render_basic_monoidal("f", "g")
    assert "Sequential Composition" in basic
    assert "Parallel (Tensor)" in basic
    assert "▼ p  (program triangle)" in basic

    eval_law = r.render_evaluator_law("my_p", L="L", M="M")
    assert "Universal Evaluator Law" in eval_law
    assert "f = {p}" in eval_law
    assert "▼ my_p" in eval_law

    fp = r.render_fixed_point_construction("succ")
    assert "Fixed Point Construction" in fp
    assert "Paper I, Lemma 6.2 + Proposition 6.1" in fp
    assert "Δ" in fp
    assert "Φ" in fp or "phi" in fp.lower()

    comon = r.render_data_service_comonoid()
    assert "Data Services — Commutative Comonoid" in comon
    assert "δ ∘ p = p ⊗ p" in comon

    # render_diagram dispatch
    d_fp = StringDiagram(fork(XI), title="fixed_point_demo")
    dispatched = r.render_diagram(d_fp)
    assert "Fixed Point" in dispatched or "Φ" in dispatched


def test_from_morphism_and_explicit_paper_diagram_construction() -> None:
    """Build the evaluator law fragment and fixed-point using builders (integration)."""
    L, M, Xi = Object("L"), Object("M"), XI
    p_tri = triangle("p42", Xi)
    u_box = box("u^L_M", src=Xi, tgt=M)

    # Manual tensor+seq (as in diagrams/examples.py)
    fragment = StringDiagram( tensor(p_tri, wire(L)), title="evaluator_law_fragment" )
    assert "evaluator" in fragment.title.lower()

    # from_morphism
    def dummy(x): return x
    morph = Morphism("agent_step", Xi, M, impl=dummy, program_code="policy42")
    d = from_morphism(morph)
    assert isinstance(d, StringDiagram)
    assert "agent_step" in d.title

    assert_diagram_reproduces_paper_figure(fragment, "evaluator law fragment")


# =============================================================================
# Models layer smoke (via direct submodule imports + now-complete builders)
# =============================================================================

def test_models_resources_classes_direct_import() -> None:
    """Smoke the resource modeling primitives (Paper II inspiration + AI safety use)."""
    tb = models_resources.TokenBudget(limit=100, used=10)
    assert tb.remaining() == 90
    tb2 = tb.consume(5)
    assert tb2.used == 15

    cs = models_resources.ComputeStep("forward", cost_units=3)
    m = cs.to_morphism(XI, Object("Out"))
    assert "compute_step" in m.program_code  # type: ignore[operator]

    chan = models_resources.InformationChannel("obs", copyable=True)
    v1, v2 = chan.apply_copy("secret_policy")
    assert v1 == v2
    chan.apply_delete("x")

    oneway = models_resources.OneWayTransform("sanitize", src=XI, tgt=XI, hardness="high")
    om = oneway.to_morphism()
    assert om.program_code is None or "oneway" in (om.program_code or "")


def test_models_agents_classes_direct_import_and_copy_semantics() -> None:
    """Smoke agent primitives + explicit Δ on MemoryState / policy (key safety idiom)."""
    tc = models_agents.ToolCall("search", cost_tokens=120, description="web")
    tm = tc.to_morphism(Object("Ctx"), Object("Obs"))
    assert "tool_def" in tm.program_code  # type: ignore[operator]
    assert DataService.is_basic_data(tm.program_code)

    mem = models_agents.MemoryState("ctx", content={"policy": "copied"})
    m1, m2 = mem.copy()
    assert isinstance(m1, models_agents.MemoryState)
    assert m1.content == m2.content

    step = models_agents.AgentStep(morph=tm, copied_policy=True, resource_notes=["Δ"])
    assert step.copied_policy

    # ReActCycle construction (no Diagram yet)
    cycle = models_agents.ReActCycle(
        cycle_id=0,
        reason_step=step,
        tool_steps=[],
        observe_step=step,
        memory_before=mem,
        memory_after=mem,
    )
    assert len(cycle.to_morphisms()) == 1


def test_models_builders_succeed_with_complete_reasoning_layer() -> None:
    """High-level builders now succeed (reasoning.Diagram + supporting classes
    are fully implemented and re-exported). Exercises the full agent/resource
    modeling + diagram emission path. Matches the positive coverage in
    test_models.py. No longer a gap.
    """
    d_react = models_agents.build_simple_react_diagram(["search", "calc"], cycles=1)
    assert hasattr(d_react, "to_mermaid")
    assert hasattr(d_react, "steps")
    steps = getattr(d_react, "steps", [])
    assert len(steps) >= 3, "ReAct builder should produce reason+tool+observe at min"
    mmd = d_react.to_mermaid()
    assert "graph TD" in mmd or "ReAct" in mmd
    assert "▼" in mmd or "policy" in mmd.lower() or "AgentPolicy" in mmd

    d_tok = models_resources.model_token_accounting([("reason", 10), ("tool", 50)])
    assert hasattr(d_tok, "to_mermaid")
    mmd_tok = d_tok.to_mermaid()
    assert "Token" in mmd_tok or "token" in mmd_tok.lower() or "budget" in mmd_tok.lower()


# =============================================================================
# Full cross-layer: MonoidalComputer + diagrams + modeled agent step
# =============================================================================

def test_agent_step_from_morphism_with_program_code_to_diagram_and_fp() -> None:
    """End-to-end: model an agent policy as program, copy it (data service),
    build its fixed point (evaluators), render as diagram (diagrams layer).

    This is the "construction of a diagram from a modeled agent step".
    """
    mc = MonoidalComputer()
    policy_code = "ReAct_policy_v3"
    # Register a simple policy program (as would come from real agent scaffold)
    mc.register_program(policy_code, lambda ctx: {"action": "tool", "ctx": ctx})

    # 1. Data service copy on the policy (as basic data)
    p1, p2 = DataService.copy(policy_code, XI)
    assert p1 == p2 == policy_code

    # 2. Fixed point of the policy (Paper I §6)
    fp_code, fp_meaning = mc.build_fixed_point(policy_code)
    assert mc.apply(fp_code, "input") == fp_meaning

    # 3. Turn the policy Morphism into a diagram (new core API)
    policy_m = Morphism(
        "reason_with_policy",
        XI,
        Object("Action"),
        impl=lambda x: mc.apply(policy_code, x),
        program_code=policy_code,
    )
    diag = policy_m.to_diagram()
    mmd = diag.to_mermaid()
    assert "reason_with_policy" in mmd or "Box" in repr(diag)

    # 4. Also render the paper fixed-point diagram for this policy
    r = MermaidRenderer()
    paper_fp_mmd = r.render_fixed_point_construction(policy_code)
    assert_diagram_reproduces_paper_figure(paper_fp_mmd, "fixed point for agent policy")

    # 5. Construction trace audit
    trace = mc.get_construction_trace()
    assert "build_fixed_point" in trace


def test_information_channel_copy_delete_in_diagram_context() -> None:
    """Models leakage surface using DataService on channels (safety use case)."""
    chan = models_resources.InformationChannel("internal_policy", copyable=True)
    val = "top_secret_policy_code"
    c1, c2 = chan.apply_copy(val)
    assert c1 == c2

    # Can appear in a diagram as fork
    d = StringDiagram( fork(Object(chan.name)), title="policy_copy_risk" )
    mmd = d.to_mermaid()
    assert "Δ" in mmd or "fork" in mmd.lower()


# =============================================================================
# Meta
# =============================================================================

def test_integration_suite_covers_all_new_public_apis() -> None:
    """Documents that post-parallel-work public surface (core ops, diagrams builders,
    renderer paper methods, models classes via direct, integration hooks) is exercised.
    """
    assert hasattr(Morphism, "to_diagram")
    assert hasattr(Morphism, "__rshift__")
    assert hasattr(Object, "tensor")
    assert hasattr(MonoidalComputer, "register_program")
    assert hasattr(StringDiagram, "save_mmd")
    assert hasattr(MermaidRenderer, "render_fixed_point_construction")
    assert hasattr(models_agents, "ToolCall")
    assert hasattr(models_resources, "InformationChannel")
