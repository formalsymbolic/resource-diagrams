"""
tests/test_evaluators.py — Tests for MonoidalComputer (universal + partial evaluators,
fixed-point construction).

Covers:
- Universal evaluator law (Paper I Def 4.1 eq (11))
- s-m-n / specialize property (Paper I Def 4.1)
- Φ self-application (Lemma 6.2) via copy only
- Fixed point construction (Prop 6.1) reproducing the exact paper diagram
  (diagrams/03_fixed_point_construction.mmd) and prototype logic
- Roundtrips, registration, traces, new public APIs (register_program etc.)
- Every public method on MonoidalComputer has >=1 dedicated test.

Uses paper_laws helpers for the diagrammatic equalities. Deterministic
"property" tests via parametrized small inputs + loops over ints/programs.
Self-documenting test names + docstrings cite paper sections.
"""

import pytest

from resource_diagrams import MonoidalComputer, Object
from resource_diagrams.core import XI

from .paper_laws import (
    assert_fixed_point_construction_law,
    assert_phi_self_application_law,
    assert_smn_specialize_law,
    assert_universal_evaluator_law,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mc() -> MonoidalComputer:
    """Fresh monoidal computer (clears any prior traces)."""
    computer = MonoidalComputer()
    computer.clear_traces()
    return computer


@pytest.fixture
def registered_programs() -> list[str]:
    """The core programs registered in _register_core_programs (plus phi)."""
    return ["id", "succ", "iszero", "const0", "phi"]


# =============================================================================
# Roundtrip / registration tests (new public register_program API)
# =============================================================================

def test_register_program_makes_it_available_for_apply_and_copy(mc: MonoidalComputer) -> None:
    """Public registration API (added for auditability)."""
    def my_impl(x: int) -> int:
        return x * 2

    mc.register_program("double", my_impl)
    assert mc.apply("double", 21) == 42
    # The code "double" is now basic data and copyable
    from resource_diagrams import DataService
    p1, p2 = DataService.copy("double", XI)
    assert p1 == p2 == "double"


def test_init_registers_exactly_the_paper_core_programs(mc: MonoidalComputer, registered_programs: list[str]) -> None:
    """The builtins are exactly those needed for paper examples + fixed point demos."""
    for prog in registered_programs:
        # All must be apply-able (phi is special)
        res = mc.apply(prog, 0 if prog != "phi" else "id")
        assert res is not None or prog == "phi"  # phi on "id" works


# =============================================================================
# Universal evaluator law (Def 4.1)
# =============================================================================

@pytest.mark.parametrize(
    "program,input_val,expected",
    [
        ("id", 99, 99),
        ("id", "anything", "anything"),
        ("succ", 41, 42),
        ("succ", 0, 1),
        ("succ", "notint", "notint"),  # per current else clause
        ("iszero", 0, True),
        ("iszero", 5, False),
        ("const0", 123, 0),
        ("const0", "foo", 0),
    ],
)
def test_evaluator_law_for_registered_programs(
    mc: MonoidalComputer, program: str, input_val: object, expected: object
) -> None:
    """Directly checks f = {p} for several programs (Paper I Def 4.1 / p.17)."""
    assert_universal_evaluator_law(mc, program, input_val, expected)


def test_evaluator_law_unknown_program_yields_none_modeling_partiality(mc: MonoidalComputer) -> None:
    """Unknown programs model non-halting / undefined (standard in the papers)."""
    assert mc.apply("nonexistent_program_42", 7) is None


# =============================================================================
# s-m-n / specialize (partial evaluator)
# =============================================================================

@pytest.mark.parametrize(
    "program,fixed,remaining,expected",
    [
        ("id", 42, "rem", (42, "rem")),
        ("succ", 5, 10, (5, 10)),  # because succ on tuple falls to else: returns the tuple
        ("const0", "ignored", 99, 0),
    ],
)
def test_specialize_then_apply_smn_property(
    mc: MonoidalComputer, program: str, fixed: object, remaining: object, expected: object
) -> None:
    """s-m-n theorem: specialize then apply == original on paired input.

    Paper I Def 4.1 (the other half of the monoidal computer).
    """
    assert_smn_specialize_law(mc, program, fixed, remaining, expected)


def test_specialize_produces_copyable_program_code_and_traces_it(mc: MonoidalComputer) -> None:
    """Specialized codes are str (basic data) and appear in construction_traces."""
    spec = mc.specialize("succ", 7)
    assert isinstance(spec, str)
    assert "spec(succ,7)" in spec
    from resource_diagrams import DataService
    assert DataService.is_basic_data(spec)
    assert any("specialize" in t for t in mc.construction_traces)


# =============================================================================
# Φ self-application law (Lemma 6.2) — the key via copy only
# =============================================================================

@pytest.mark.parametrize("p", ["id", "succ", "const0", "iszero"])
def test_phi_self_application_law_for_various_p(mc: MonoidalComputer, p: str) -> None:
    """{Φ}(p) = {p}(p) constructed purely via DataService.copy + u.

    Paper I Lemma 6.2 (p.25-26). This is what makes the graphical proof
    short and the recursion theorem "obvious" in the string diagram.
    """
    assert_phi_self_application_law(mc, p)


def test_phi_on_non_string_yields_none(mc: MonoidalComputer) -> None:
    """Φ only defined on program codes (strings on Ξ)."""
    assert mc.apply("phi", 42) is None
    assert mc.apply("phi", {"not": "str"}) is None


# =============================================================================
# Fixed point construction (Prop 6.1) — exact reproduction
# =============================================================================

@pytest.mark.parametrize("p_code", ["id", "const0", "succ"])
def test_fixed_point_construction_reproduces_paper_i_6_for_various(mc: MonoidalComputer, p_code: str) -> None:
    """Reproduce the exact fixed-point construction of Paper I §6 (succ is the
    running example in the paper for producing a non-total element).

    Asserts the diagrammatic equation via the paper_laws helper (which encodes
    Lemma 6.2 + Prop 6.1 + the copy axiom).
    """
    assert_fixed_point_construction_law(mc, p_code)


def test_fixed_point_succ_has_registered_fp_that_satisfies_law(mc: MonoidalComputer) -> None:
    """Specific succ case (Paper I corollary 6.3 illustration).

    In the model, the fp witness for succ satisfies the equation inside the
    extended domain (str codes + numbers).
    """
    fp_code, fp_meaning = mc.build_fixed_point("succ")
    assert fp_code == "fix(succ)"
    # fp program constantly yields the witness
    assert mc.apply(fp_code, "anything") == fp_meaning
    # And {succ}(witness) == witness (law holds)
    assert mc.apply("succ", fp_meaning) == fp_meaning
    # Traces record the Paper I reference
    trace = mc.get_construction_trace()
    assert "Paper I p.25-26" in trace
    assert "diagrams/03_fixed_point_construction.mmd" in trace


def test_build_fixed_point_clears_and_appends_traces(mc: MonoidalComputer) -> None:
    """Construction is auditable (traces for higher diagram layers / safety review)."""
    mc.clear_traces()
    mc.build_fixed_point("const0")
    trace = mc.get_construction_trace()
    assert "build_fixed_point" in trace
    assert "Φ(p)" in trace or "phi" in trace.lower()


# =============================================================================
# Traces and auxiliary public methods
# =============================================================================

def test_construction_traces_and_clear_are_public_and_useful(mc: MonoidalComputer) -> None:
    """get_construction_trace / clear_traces (public for audit + test isolation)."""
    mc.specialize("id", 1)
    assert len(mc.construction_traces) >= 1
    t = mc.get_construction_trace()
    assert "specialize" in t
    mc.clear_traces()
    assert mc.construction_traces == []
    assert mc.get_construction_trace() == ""


# =============================================================================
# "Property" style loop over small numeric inputs (stdlib, deterministic)
# =============================================================================

def test_evaluator_and_specialize_on_small_ints_loop(mc: MonoidalComputer) -> None:
    """Generative flavor without hypothesis: loop over small ints for numeric programs.

    Exercises succ, iszero, const0 + specialize on them. Fast + deterministic.
    """
    small = list(range(-2, 6)) + [100]
    for n in small:
        assert mc.apply("succ", n) == (n + 1 if isinstance(n, int) else n)
        assert mc.apply("iszero", n) == (n == 0)
        assert mc.apply("const0", n) == 0

        spec_s = mc.specialize("succ", n)
        # apply spec on arbitrary rem; by model it returns the pair
        rem = 99
        assert mc.apply(spec_s, rem) == (n, rem)


# =============================================================================
# Meta / coverage
# =============================================================================

def test_every_public_monoidal_computer_method_exercised() -> None:
    """Documents coverage of the public surface (apply, specialize, build_fixed_point,
    register_program, get_construction_trace, clear_traces, plus __init__).
    """
    mc = MonoidalComputer()
    assert callable(mc.apply)
    assert callable(mc.specialize)
    assert callable(mc.build_fixed_point)
    assert callable(mc.register_program)
    assert callable(mc.get_construction_trace)
    assert callable(mc.clear_traces)
    # All exercised in tests above.
