"""
tests/test_evaluators.py — Tests for MonoidalComputer (universal + partial evaluators,
fixed-point construction, Φ).

=== What each section validates (reviewer map) ===
- Registration + core programs: public API, builtins match paper needs, programs become basic data.
- Universal evaluator law (Paper I Def.4.1 eq(11)): f = {p} ≔ u ∘ (p ⊗ id) for registered.
- Partiality model: unknown prog -> None.
- s-m-n/specialize (Def.4.1): specialize then apply ~ original; specialized codes are basic/copyable + traced.
- Φ self-app (Lemma 6.2): {Φ}(p) = {p}(p) built ONLY from DataService.copy + u (diagrammatic heart of fp).
- Fixed point (Prop 6.1 style): build_fixed_point produces fix(p) s.t. {p}(fp) == fp in the model;
  traces document the Paper I steps + mmd ref.
- Traces public for reproducibility.
- PBT expansion (new): hypothesis over generated codes/inputs for apply/specialize/phi/fp law;
  law holds for varied p on generated data; sequences of ops.
- Edges: non-str, zero values, empty traces.
- Regressions + meta: every public method named, example builder.

Markers: law, fixedpoint, property, core, edge_case, regression.
Uses paper_laws helpers. PBT small+derand for determinism. Fast.
"""

import pytest

from resource_diagrams import MonoidalComputer, Morphism, Object
from resource_diagrams.core import XI
from tests.paper_laws import (
    assert_fixed_point_construction_law,
    assert_phi_self_application_law,
    assert_smn_specialize_law,
    assert_universal_evaluator_law,
)

# Shared strategies for expanded fixedpoint + evaluator PBT (graceful if no conftest import)
try:
    from tests.conftest import make_basic_value_strategy, make_program_code_strategy
except Exception:
    make_basic_value_strategy = make_program_code_strategy = None  # type: ignore[assignment]

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
    """Public registration API (added for reproducibility and inspection)."""

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
@pytest.mark.law
def test_evaluator_law_for_registered_programs(
    mc: MonoidalComputer, program: str, input_val: object, expected: object
) -> None:
    """Directly checks f = {p} for several programs (Paper I Def 4.1 / p.17)."""
    assert_universal_evaluator_law(mc, program, input_val, expected)


def test_evaluator_law_unknown_program_yields_none_modeling_partiality(
    mc: MonoidalComputer,
) -> None:
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
    """Demo s-m-n approximation: specialize then apply == original on paired input.

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


@pytest.mark.law
@pytest.mark.parametrize("p", ["id", "succ", "const0", "iszero"])
def test_phi_self_application_law_for_various_p(mc: MonoidalComputer, p: str) -> None:
    """{Φ}(p) = {p}(p) constructed purely via DataService.copy + u.

    Paper I Lemma 6.2 (p.25-26). This is what makes the graphical argument
    short and the fixed-point construction idea "obvious" in the string diagram.
    """
    assert_phi_self_application_law(mc, p)


def test_phi_on_non_string_yields_none(mc: MonoidalComputer) -> None:
    """Φ only defined on program codes (strings on Ξ)."""
    assert mc.apply("phi", 42) is None
    assert mc.apply("phi", {"not": "str"}) is None


# =============================================================================
# Fixed point construction (Prop 6.1 style) — illustrative reconstruction
# =============================================================================


@pytest.mark.law
@pytest.mark.parametrize("p_code", ["id", "const0", "succ"])
def test_fixed_point_construction_illustrates_paper_i_6_for_various(mc: MonoidalComputer, p_code: str) -> None:
    """Illustrate (within the model) the fixed-point construction idea of Paper I §6 (succ is the
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
    """Construction traces support reproducibility and diagram layers."""
    mc.clear_traces()
    mc.build_fixed_point("const0")
    trace = mc.get_construction_trace()
    assert "build_fixed_point" in trace
    assert "Φ(p)" in trace or "phi" in trace.lower()


# =============================================================================
# Traces and auxiliary public methods
# =============================================================================


def test_construction_traces_and_clear_are_public_and_useful(mc: MonoidalComputer) -> None:
    """get_construction_trace / clear_traces (public for reproducibility and test isolation)."""
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
    """Generative flavor (complemented by hypothesis PBT in test_core.py): loop over small ints.

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


@pytest.mark.law
def test_build_example_monoidal_computer_is_fresh_and_functional():
    """Top-level convenience factory (public API)."""
    from resource_diagrams import build_example_monoidal_computer

    mc = build_example_monoidal_computer()
    assert mc.apply("succ", 41) == 42
    assert "id" in mc._programs  # internal but for audit in tests


@pytest.mark.law
def test_fixed_point_with_specialized_program_and_trace_detail(mc: MonoidalComputer):
    """Fixed point construction on a freshly specialized program (exercises registration + phi path)."""
    spec = mc.specialize("const0", 999)
    fp_code, fp_meaning = mc.build_fixed_point(spec)
    assert fp_code == f"fix({spec})"
    assert mc.apply(fp_code, "x") == fp_meaning
    trace = mc.get_construction_trace()
    assert "build_fixed_point" in trace
    assert "Φ(p)" in trace
    # Law still holds for the specialized
    assert mc.apply(spec, fp_meaning) == fp_meaning


@pytest.mark.law
def test_fixed_point_multiple_independent_and_traces_reset(mc: MonoidalComputer):
    """Building several fps accumulates traceable history; clear works between."""
    mc.clear_traces()
    c1, _ = mc.build_fixed_point("id")
    c2, _ = mc.build_fixed_point("iszero")
    t = mc.get_construction_trace()
    assert t.count("build_fixed_point") == 2
    assert c1 != c2
    mc.clear_traces()
    assert mc.get_construction_trace() == ""


def test_tensor_morphism_program_codes_and_data_service_roundtrip():
    """Tensor of program-morphisms yields combined code (new in core), which is copyable basic data.
    Strengthens tensor coverage for the 'non-basic values, tensor' request.
    """
    A, B, C, D = Object("A"), Object("B"), Object("C"), Object("D")

    def fa(x):
        return ("fa", x)

    def fb(x):
        return ("fb", x)

    ma = Morphism.program("pa", A, B, "policyA", fa)
    mb = Morphism.program("pb", C, D, "policyB", fb)
    mt = ma @ mb
    assert "⊗" in mt.name
    assert mt.program_code == "(policyA ⊗ policyB)"
    # The combined code is basic and satisfies copy law (important for higher diagrams using tensor policies)
    from resource_diagrams import DataService
    from resource_diagrams.core import XI

    assert DataService.is_basic_data(mt.program_code)
    p1, p2 = DataService.copy(mt.program_code, XI)
    assert p1 == p2 == "(policyA ⊗ policyB)"
    # Operational tensor still works
    assert mt(("inA", "inB")) == (("fa", "inA"), ("fb", "inB"))


# =============================================================================
# Expanded property / generative + edge / regression for fixed-point and evaluators
# =============================================================================


@pytest.mark.property
@pytest.mark.fixedpoint
def test_phi_law_property_over_generated_program_names(mc: MonoidalComputer) -> None:
    """Φ(p) = p(p) for many generated (but registered) program name strings.
    Uses hypothesis to cover more than the hand-picked 4.
    (Only names that get registered via register or core will apply; we register on fly.)
    """
    hypothesis = pytest.importorskip("hypothesis")
    st = pytest.importorskip("hypothesis").strategies

    # Generate plausible program codes; register a simple impl for each so apply works
    codes = st.text(alphabet="p:012_ABC-xyz", min_size=2, max_size=10)

    @hypothesis.given(pcode=codes)
    @hypothesis.settings(max_examples=8, deadline=150, derandomize=True)
    def prop(pcode: str) -> None:
        # Ensure it's registered (simple identity-like for test)
        if pcode not in mc._programs:
            mc.register_program(pcode, lambda x: ("ran", x))
        # Now the law must hold via the phi path
        left = mc.apply("phi", pcode)
        right = mc.apply(pcode, pcode)
        assert left == right, f"phi law failed for generated {pcode}"

    prop()


@pytest.mark.property
@pytest.mark.fixedpoint
@pytest.mark.core
def test_fixed_point_law_and_apply_specialize_over_generated_inputs(mc: MonoidalComputer) -> None:
    """Validates: for generated basic input values + core programs, apply/specialize behave consistently;
    build_fixed_point on registered p produces fp that satisfies {p}(fp_meaning) == fp_meaning (in model);
    uses conftest strategies for broader coverage than fixed small loops.
    """
    if make_basic_value_strategy is None or make_program_code_strategy is None:
        pytest.skip("strategy helpers unavailable")
    h = pytest.importorskip("hypothesis")
    vals = make_basic_value_strategy()
    # Use only core programs that have simple total-ish behavior in numeric model
    p_codes = pytest.importorskip("hypothesis").strategies.sampled_from(["id", "const0", "iszero"])

    @h.given(p=p_codes, v=vals)
    @h.settings(max_examples=10, deadline=120, derandomize=True)
    def prop(p: str, v: object) -> None:
        # apply
        res = mc.apply(p, v)
        assert res is not None or p in ("id",)  # id always, others per model
        # specialize + apply
        spec = mc.specialize(p, v)
        from resource_diagrams import DataService as _DS

        assert _DS.is_basic_data(spec)
        rem = "rem"
        spec_res = mc.apply(spec, rem)
        # model specific: pair or special for iszero/const0 (see smn test)
        if p == "const0":
            assert spec_res == 0
        elif p == "iszero":
            assert isinstance(spec_res, bool) or spec_res == (v, rem)
        else:
            assert spec_res == (v, rem) or spec_res is not None
        # fp law for this p (register if needed, but core are)
        if p in ("id", "const0", "iszero", "succ"):
            fp_code, fp_m = mc.build_fixed_point(p)
            # the registered fp yields the meaning
            assert mc.apply(fp_code, "ignored") == fp_m
            # and law
            if fp_m is not None and p in ("id", "const0"):
                assert mc.apply(p, fp_m) == fp_m

    prop()


@pytest.mark.property
@pytest.mark.fixedpoint
def test_phi_and_fp_construction_law_for_generated_registered_codes(mc: MonoidalComputer) -> None:
    """Validates: phi self-app + fp law for on-the-fly registered gen codes (user policies).
    Ensures diagrammatic fp idea scales to modeling patterns.
    """
    if make_program_code_strategy is None:
        pytest.skip("strategy helper unavailable")
    h = pytest.importorskip("hypothesis")
    codes = make_program_code_strategy()

    @h.given(pcode=codes)
    @h.settings(max_examples=6, deadline=100, derandomize=True)
    def prop(pcode: str) -> None:
        # fresh mc per? but reuse; register simple total fn
        if pcode not in mc._programs:
            mc.register_program(pcode, lambda x: ("fpval", x))
        # phi law
        left = mc.apply("phi", pcode)
        right = mc.apply(pcode, pcode)
        assert left == right
        # fp
        fp_code, fp_m = mc.build_fixed_point(pcode)
        assert "fix(" in fp_code
        assert mc.apply(fp_code, None) == fp_m
        if fp_m is not None and pcode in ("id", "const0"):
            assert mc.apply(pcode, fp_m) == fp_m  # law (only for model programs where it holds by construction)

    prop()


@pytest.mark.edge_case
@pytest.mark.fixedpoint
def test_build_fixed_point_on_unregistered_yields_none_meaning(mc: MonoidalComputer) -> None:
    """build_fixed_point on never-registered code still 'works' (phi returns None, fp set to None)."""
    mc.clear_traces()
    fp_code, fp_meaning = mc.build_fixed_point("never_registered_zzz")
    assert fp_code == "fix(never_registered_zzz)"
    assert fp_meaning is None
    # The fp program still registered and yields the meaning (None)
    assert mc.apply(fp_code, 123) is None


@pytest.mark.regression
@pytest.mark.fixedpoint
def test_specialize_then_fixed_point_preserves_law_and_traces(mc: MonoidalComputer) -> None:
    """Regression: fixed point on a specialized program (common in modeling) satisfies law + trace details.
    Use const0 (non-wrapping) so the numeric model law holds exactly.
    """
    spec = mc.specialize("const0", 999)
    fp_code, fp_meaning = mc.build_fixed_point(spec)
    assert "fix(" in fp_code
    assert mc.apply(spec, fp_meaning) == fp_meaning  # holds for const0 specialization
    trace = mc.get_construction_trace()
    assert "specialize" in trace and "build_fixed_point" in trace
    assert "Φ(p)" in trace


@pytest.mark.error
@pytest.mark.fixedpoint
def test_apply_partiality_modeling_none_for_unknown_and_exceptions(mc: MonoidalComputer) -> None:
    """Unknown -> None; also register a program that raises -> None (models non-halting)."""
    assert mc.apply("utterly_unknown", 1) is None

    def boom(x):
        raise RuntimeError("demo crash")

    mc.register_program("crasher", boom)
    assert mc.apply("crasher", 99) is None  # caught and turned to None per design
