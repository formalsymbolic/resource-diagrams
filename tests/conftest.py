"""
Shared pytest fixtures, markers, and hypothesis strategies for the resource-diagrams test suite.

This conftest enables:
- Consistent, documented fixtures for core objects (XI, N, B, I, sample sensitive/policy).
- Reusable hypothesis strategies for property tests (object names, basic data, program codes, cycles, tool lists).
  New: make_program_code_strategy, make_small_positive_int_strategy, make_tool_names_strategy.
- Automatic registration of custom markers (see pyproject.toml for full list: law/safety/property/.../regression).
- Rich Safety test helpers: PathSensitivityCase + many concrete cases (min_policy_fork, path_sensitive_reach_{un,}guarded,
  multi_type_forks, termination_effects, + new: parallel_only_sensitive, sequential_mixed_forks_termination,
  stem_on_policy, reasoner_box_not_tool_reach, multi_stem_chain_termination).
  These drive comprehensive path-sensitivity, fork-classif (all 6 types), termination (selective remove from live), report, serialization tests.
- Fast/deterministic defaults: hypothesis max_examples capped + derandomize=True used throughout PBT.
- All fixtures self-documenting with "Validates"/"Exercises" in consuming test docstrings.

All fixtures function-scoped (except session canonicals); importing registers markers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from resource_diagrams import Object
from resource_diagrams.core import XI, B, I, N
from resource_diagrams.diagrams import (
    Box,
    StringDiagram,
    box,
    fork,
    seq,
    stem,
    tensor,
    triangle,
    wire,
)
from resource_diagrams.diagrams.safety import SafetyAnalyzer

# =============================================================================
# Core canonical objects (used across core, data_service, evaluators, safety, models)
# =============================================================================


@pytest.fixture(scope="session")
def xi() -> Object:
    """Universal type Ξ (programs live here as data)."""
    return XI


@pytest.fixture(scope="session")
def n() -> Object:
    """Natural numbers N."""
    return N


@pytest.fixture(scope="session")
def b() -> Object:
    """Booleans B."""
    return B


@pytest.fixture(scope="session")
def unit() -> Object:
    """Monoidal unit I."""
    return I


@pytest.fixture
def sample_objects() -> list[Object]:
    """Small set of distinct named objects for tensor/composition tests."""
    return [Object("A"), Object("B"), Object("C"), Object("Policy"), Object("Secret")]


# =============================================================================
# Data / program values for DataService + fixed-point tests
# =============================================================================


@pytest.fixture
def basic_data_values() -> list[Any]:
    """Representative basic data (str/int/bool/tuple) that obey copy laws structurally."""
    return [
        0,
        42,
        -7,
        "",
        "policy_v1",
        "user:secret:42",
        True,
        False,
        (1, "x"),
        ("p", 99, False),
    ]


@pytest.fixture
def program_codes() -> list[str]:
    """Program codes (always basic data on Ξ)."""
    return ["id", "succ", "phi", "const0", "my_agent_policy_7", "critic_v2"]


@pytest.fixture
def non_basic_data_values() -> list[Any]:
    """Non-basic values exercising deepcopy vs alias-fallback paths."""
    return [{"ctx": "memory"}, ["obs1", "obs2"], object()]


# =============================================================================
# Safety / analyzer specific fixtures and builders (for comprehensive path/fork/termination tests)
# =============================================================================


@dataclass
class PathSensitivityCase:
    """Container for a minimal diagram + expected analyzer signals (for doc + asserts)."""

    title: str
    diagram: StringDiagram
    min_forks: int = 0
    min_stems: int = 0
    expect_reach: bool = False
    expect_persist: bool | None = None
    fork_types: set[str] | None = None


@pytest.fixture
def policy_obj() -> Object:
    return Object("Policy")


@pytest.fixture
def sensitive_obj() -> Object:
    return Object("UserSecret")


@pytest.fixture
def context_obj() -> Object:
    return Object("MemoryContext")


@pytest.fixture
def observation_obj() -> Object:
    return Object("ObservationResult")


@pytest.fixture
def resource_obj() -> Object:
    return Object("TokenBudget")


@pytest.fixture
def plain_data_obj() -> Object:
    return Object("PlainData")


def _make_tool_box(label: str = "tool:call", src: Object | None = None) -> Box:
    if src is None:
        src = Object("In")
    return box(label, src=src, program_code="tool:search:exfil")


@pytest.fixture
def minimal_policy_fork_diagram(policy_obj: Object) -> StringDiagram:
    """Simplest policy fork (for basic fork_type + count)."""
    pol_tri = triangle("AgentPolicy", policy_obj)
    f = fork(policy_obj)
    root = seq(pol_tri, f)
    return StringDiagram(root, title="min_policy_fork")


@pytest.fixture
def path_sensitive_reach_unguarded(
    policy_obj: Object, sensitive_obj: Object, context_obj: Object
) -> PathSensitivityCase:
    """Policy fork + sensitive reaching a tool Box with no stem after (high risk path)."""
    pol_tri = triangle("AgentPolicy", policy_obj)
    sec_wire = wire(sensitive_obj, "one-way-secret")
    entry = tensor(pol_tri, sec_wire)
    f = fork(policy_obj)
    tool = _make_tool_box("Tool[exfil]", src=context_obj)
    root = seq(seq(entry, f), tool)
    sd = StringDiagram(root, title="path_reach_unguarded")
    return PathSensitivityCase(
        title="path_reach_unguarded",
        diagram=sd,
        min_forks=1,
        min_stems=0,
        expect_reach=True,
        expect_persist=True,
        fork_types={"policy"},
    )


@pytest.fixture
def path_sensitive_reach_guarded(policy_obj: Object, sensitive_obj: Object, context_obj: Object) -> PathSensitivityCase:
    """Same structure + explicit Stem(⊤) after the tool on the sensitive leg (termination)."""
    # Rebuild guarded (dupe construction to avoid calling other fixture fn directly)
    pol_tri = triangle("AgentPolicy", policy_obj)
    sec_wire = wire(sensitive_obj, "one-way-secret")
    entry = tensor(pol_tri, sec_wire)
    f = fork(policy_obj)
    tool = _make_tool_box("Tool[exfil]", src=context_obj)
    s = stem(sensitive_obj)
    root = seq(seq(seq(entry, f), tool), s)
    sd = StringDiagram(root, title="path_reach_guarded")
    return PathSensitivityCase(
        title="path_reach_guarded",
        diagram=sd,
        min_forks=1,
        min_stems=1,
        expect_reach=True,
        expect_persist=False,  # terminated
        fork_types={"policy"},
    )


@pytest.fixture
def multi_type_forks_diagram(
    policy_obj: Object,
    sensitive_obj: Object,
    context_obj: Object,
    observation_obj: Object,
    resource_obj: Object,
    plain_data_obj: Object,
) -> StringDiagram:
    """Diagram with one Fork of each classify-able type (policy, sensitive, context, observation, resource, data)."""
    roots = []
    for obj, prog in [
        (policy_obj, "PolicyFork"),
        (sensitive_obj, "SensitiveFork"),
        (context_obj, "ContextFork"),
        (observation_obj, "ObsFork"),
        (resource_obj, "ResFork"),
        (plain_data_obj, "DataFork"),
    ]:
        tri = triangle(prog, obj)
        f = fork(obj)
        roots.append(seq(tri, f))
    # Parallel all via nested tensor (exercises tensor union in flow)
    combined = roots[0]
    for r in roots[1:]:
        combined = tensor(combined, r)
    return StringDiagram(combined, title="multi_type_forks")


@pytest.fixture
def termination_effects_diagram(policy_obj: Object, sensitive_obj: Object) -> StringDiagram:
    """Sequential sensitive fork, use, stem, then another box that should not see the sensitive live."""
    tri = triangle("P", policy_obj)
    f = fork(sensitive_obj)  # fork on sensitive to exercise
    tool1 = _make_tool_box("Tool1", src=sensitive_obj)
    s = stem(sensitive_obj)
    tool2 = _make_tool_box("Tool2", src=sensitive_obj)
    root = seq(seq(seq(seq(tri, f), tool1), s), tool2)
    return StringDiagram(root, title="termination_effects")


@pytest.fixture
def analyzer_for(diagram: StringDiagram) -> SafetyAnalyzer:
    """Convenience: fresh analyzer for a given diagram (used in parametrized safety tests)."""
    return SafetyAnalyzer(diagram)


# --- Additional PathSensitivityCase fixtures for comprehensive coverage of path sensitivity,
# different fork types (seq vs tensor), termination on policy vs sensitive, reasoner contexts,
# parallel-only influence, and mixed termination. These enable exhaustive report/edge tests
# without duplication in test bodies. All deterministic. ---
# (reuses the module-level _make_tool_box defined above for the original fixtures)


@pytest.fixture
def parallel_only_sensitive_reach_case(policy_obj: Object, sensitive_obj: Object) -> PathSensitivityCase:
    """Tensor of policy-fork and sensitive-wire; the sensitive lives only on one parallel leg.
    Tests that reach recording is branch-local (path sensitivity via tensor union)."""
    pol_tri = triangle("P", policy_obj)
    f = fork(policy_obj)
    sec_w = wire(sensitive_obj, "priv")
    tool = _make_tool_box("ToolPar", src=sensitive_obj)
    # (pol_tri ; f)  ⊗  (sec_w ; tool)   -- sensitive reaches tool on its leg, policy on other
    left = seq(pol_tri, f)
    right = seq(sec_w, tool)
    root = tensor(left, right)
    sd = StringDiagram(root, title="parallel_sensitive_only")
    return PathSensitivityCase(
        title="parallel_sensitive_only",
        diagram=sd,
        min_forks=1,
        min_stems=0,
        expect_reach=True,
        expect_persist=True,
        fork_types={"policy"},
    )


@pytest.fixture
def sequential_mixed_forks_termination_case(
    policy_obj: Object, sensitive_obj: Object, context_obj: Object
) -> PathSensitivityCase:
    """Seq of policy fork, sensitive fork, tool (under both?), stem on sensitive, downstream tool.
    Exercises sequential live-passing + selective termination (sensitive removed, policy may persist)."""
    p_tri = triangle("Policy", policy_obj)
    pf = fork(policy_obj)
    s_tri = triangle("Sens", sensitive_obj)  # to give sensitive a triangle origin
    sf = fork(sensitive_obj)
    tool1 = _make_tool_box("ToolMixed", src=context_obj)
    s = stem(sensitive_obj)
    tool2 = _make_tool_box("ToolAfterStem", src=context_obj)
    root = seq(seq(seq(seq(seq(p_tri, pf), s_tri), sf), tool1), s)
    root = seq(root, tool2)
    sd = StringDiagram(root, title="seq_mixed_forks_term")
    return PathSensitivityCase(
        title="seq_mixed_forks_term",
        diagram=sd,
        min_forks=2,
        min_stems=1,
        expect_reach=True,
        expect_persist=False,
        fork_types={"policy", "sensitive"},
    )


@pytest.fixture
def stem_on_policy_case(policy_obj: Object) -> PathSensitivityCase:
    """Policy fork followed by stem on the policy object itself.
    Validates that stems classify and remove 'policy' influences too (termination effects on policy paths)."""
    tri = triangle("Pol", policy_obj)
    f = fork(policy_obj)
    s = stem(policy_obj)
    root = seq(seq(tri, f), s)
    sd = StringDiagram(root, title="stem_on_policy")
    return PathSensitivityCase(
        title="stem_on_policy",
        diagram=sd,
        min_forks=1,
        min_stems=1,
        expect_reach=False,
        expect_persist=False,
        fork_types={"policy"},
    )


@pytest.fixture
def reasoner_box_not_tool_reach_case(policy_obj: Object, sensitive_obj: Object) -> PathSensitivityCase:
    """Sensitive + policy reach a 'reason' Box (is_tool_or_reasoner_context true via 'reason' kw)
    but not a 'tool' labeled one; verifies reach recording for reasoner contexts too."""
    tri = triangle("AgentPolicy", policy_obj)
    sw = wire(sensitive_obj, "s")
    entry = tensor(tri, sw)
    f = fork(policy_obj)
    reason = box("reasoner:think", src=Object("Ctx"), program_code="reason:step:1")
    root = seq(seq(entry, f), reason)
    sd = StringDiagram(root, title="reasoner_reach")
    return PathSensitivityCase(
        title="reasoner_reach",
        diagram=sd,
        min_forks=1,
        min_stems=0,
        expect_reach=True,
        expect_persist=True,
        fork_types={"policy"},
    )


@pytest.fixture
def multi_stem_chain_termination_case(sensitive_obj: Object) -> PathSensitivityCase:
    """Chain of use-stem-use-stem on sensitive to test repeated removal + no false persist."""
    w = wire(sensitive_obj, "s")
    t1 = _make_tool_box("T1", src=sensitive_obj)
    s1 = stem(sensitive_obj)
    t2 = _make_tool_box("T2", src=sensitive_obj)
    s2 = stem(sensitive_obj)
    root = seq(seq(seq(seq(w, t1), s1), t2), s2)
    sd = StringDiagram(root, title="multi_stem_chain")
    return PathSensitivityCase(
        title="multi_stem_chain",
        diagram=sd,
        min_forks=0,
        min_stems=2,
        expect_reach=True,
        expect_persist=False,
        fork_types=set(),
    )


# =============================================================================
# Hypothesis strategies (for property expansion; keep small for speed/determinism)
# =============================================================================


def get_hypothesis_strategies():
    """Lazy import of hypothesis.strategies inside tests that need PBT (avoids hard dep at collection)."""
    hypothesis = pytest.importorskip("hypothesis", reason="hypothesis not installed")
    return hypothesis, hypothesis.strategies


# Small name strategy for Object/Morphism generation (readable, bounded)
small_name = None  # populated on first use in props via get_...


def make_small_name_strategy():
    h, st = get_hypothesis_strategies()
    return st.text(alphabet="ABCDEabcde012_", min_size=1, max_size=4)


# Basic values strategy (covers copy law etc.)
def make_basic_value_strategy():
    h, st = get_hypothesis_strategies()
    return st.one_of(
        st.integers(min_value=-100, max_value=100),
        st.text(max_size=8),
        st.booleans(),
        st.tuples(st.integers(min_value=0, max_value=5), st.text(max_size=3)),
    )


def make_program_code_strategy():
    """Strategy for program codes (str on Ξ) used in fixed-point, phi, specialize, DataService laws, modeling."""
    h, st = get_hypothesis_strategies()
    return st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_:-", min_size=1, max_size=12)


def make_small_positive_int_strategy(min_value: int = 1, max_value: int = 5):
    """Small positive ints for cycles, depths, agent counts — keeps PBT fast/deterministic."""
    h, st = get_hypothesis_strategies()
    return st.integers(min_value=min_value, max_value=max_value)


def make_tool_names_strategy(max_tools: int = 4):
    """Small lists of tool names for ReAct/hierarchical/etc builder PBT."""
    h, st = get_hypothesis_strategies()
    name = st.text(alphabet="searchcalcwebdbexec", min_size=2, max_size=6)
    return st.lists(name, min_size=0, max_size=max_tools, unique=True)


# =============================================================================
# Advanced strategies for expanded PBT (SafetyAnalyzer path-sens/fork/term/report/ser,
# modeling patterns, tensor/comp/DataService/fixedpoint cross interactions).
# Bounded, derandomized, small examples for speed + 100% determinism.
# =============================================================================


def make_small_diagram_element_strategy():
    """Generates small bounded-depth DiagramElement trees exercising Wire/Box/Tri/Fork/Stem + Seq/Tensor.

    Used for property tests of SafetyAnalyzer (live flow, classify on 6 types, termination selective remove,
    reach recording under policy_copy, report gen decision tree, to_dict/ser invariants) and integration.
    Trees are small (depth<=2) + limited branching to keep PBT fast/deterministic.
    Reuses diagram builders already imported at top of conftest.
    """
    h, st = get_hypothesis_strategies()
    obj_st = st.builds(Object, st.text(alphabet="PoliSecCtxObsResDat", min_size=2, max_size=4))

    # Primitive leaves (small variety)
    wire_st = st.builds(wire, obj_st, st.text(max_size=5) | st.just(None))
    box_st = st.builds(
        box,
        st.text(alphabet="reasontoolsearchcallexecdecide", min_size=3, max_size=8),
        src=obj_st | st.just(None),
        program_code=st.text(alphabet="p:tool_policy_agent", min_size=0, max_size=10) | st.just(None),
    )
    tri_st = st.builds(triangle, st.text(alphabet="AgentPolicySubCriticTool", min_size=3, max_size=8), obj_st)
    fork_st = st.builds(fork, obj_st)
    stem_st = st.builds(stem, obj_st)

    leaf = st.one_of(wire_st, box_st, tri_st, fork_st, stem_st)

    @st.composite
    def _gen(draw):
        # Small number of leaves, fold with random seq/tensor (exercises flow recursion + tensor union + seq pass)
        n = draw(st.integers(min_value=1, max_value=3))
        leaves = [draw(leaf) for _ in range(n)]
        root = leaves[0]
        for nxt in leaves[1:]:
            comb = draw(st.sampled_from([seq, tensor]))
            root = comb(root, nxt)
        # occasional extra fork or stem on the result (for classify/term coverage)
        if draw(st.booleans()):
            extra_ctor = draw(st.sampled_from([fork, stem]))
            o = draw(obj_st)
            root = seq(root, extra_ctor(o))
        return root

    return _gen()


def make_small_string_diagram_strategy():
    """Builds a StringDiagram from small element trees + title for analyzer PBT."""
    h, st = get_hypothesis_strategies()
    elem_st = make_small_diagram_element_strategy()
    title_st = st.text(alphabet="TestDiag", min_size=3, max_size=12)
    return st.builds(StringDiagram, root=elem_st, title=title_st)


def make_modeling_builder_params_strategy():
    """Params for exercising new modeling patterns (hier/reflex/multi) + safety in PBT."""
    h, st = get_hypothesis_strategies()
    return {
        "tools": make_tool_names_strategy(3),
        "cycles": make_small_positive_int_strategy(1, 3),
        "subs": st.lists(st.text(alphabet="sub", min_size=3, max_size=5), min_size=0, max_size=2),
        "n_agents": make_small_positive_int_strategy(1, 3),
    }


# =============================================================================
# Session level: ensure hypothesis is importable for property tests (fail fast if missing in dev)
# =============================================================================


def pytest_configure(config):
    """Register markers explicitly (in addition to pyproject) and any config."""
    # Already in pyproject.ini_options; this is belt-and-suspenders for interactive runs.
    config.addinivalue_line("markers", "law: ...")
    config.addinivalue_line("markers", "safety: ...")
    # etc. (the full list lives in pyproject.toml for single source of truth)


@pytest.fixture(scope="session", autouse=True)
def _require_hypothesis_for_property_marked():
    """If any test is marked property, hypothesis must be present (dev install)."""
    # Actual importorskip happens inside the property test helpers; this is just documentation.
    pass
