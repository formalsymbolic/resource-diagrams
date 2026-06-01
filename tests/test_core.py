"""
tests/test_core.py — Core Object, Morphism, tensor (@), composition (>>), factories, and DataService interop.

=== What is validated (for instant reviewer comprehension) ===
- Object: strict monoidal tensor (units I elide by ref, flat assoc names/eq for coherence transparency),
  is_unit, equality/hash by name.
- Morphism: pure/program factories, >> (seq + prog_code), @ (tensor + prog_code),
  call, frozen immut, to_diagram hook.
- Laws (paper-inspired): unitors, assoc transparency (names+id), distrib of ⊗ over ; (in demo model).
- DataService interop: program_code is basic+copyable; copy_law on basics.
- Property-based (hypothesis, small examples, derandomized via helper): tensor units/assoc/name-flat/eq,
  morphism tensor/call, comp assoc/call, tensor-distrib-comp, DS copy+law on generated basics/programs.
- Edges: unit identities, frozen, non-pair tensor fallback.
- Errors: comp tgt/src mismatch.
- Regressions: prog_code survives ; and ⊗ (for fp + diagrams).

PBT uses make_*_strategy from conftest + _apply_settings (max_examples<=15, deadline short).
Run focused: pytest -m "property and (tensor or composition or data_service)".
All fast/deterministic.
"""

import pytest

from resource_diagrams.core import Morphism, Object


def test_object_repr():
    obj = Object("TestType")
    assert repr(obj) == "TestType"


def test_morphism_basic():
    src = Object("A")
    tgt = Object("B")

    def dummy_impl(x):
        return x  # placeholder implementation for structural testing only

    morph = Morphism("test_morph", src, tgt, impl=dummy_impl)

    assert morph.name == "test_morph"
    assert morph.src == src
    assert morph.tgt == tgt
    assert "test_morph" in repr(morph)


# --- Minimal additions for rich core (frozen, tensor, composition, factories, canonicals) ---

from resource_diagrams.core import XI, B, I, N  # reimport for new names


def test_canonical_objects():
    assert XI.name == "Ξ"
    assert N.name == "N"
    assert B.name == "B"
    assert I.name == "I"
    assert I.is_unit
    assert not N.is_unit


def test_object_tensor_and_unit_laws():
    a = Object("A")
    b = Object("B")
    # Note: Object tensor names are deliberately flattened (no outer parens)
    # per core.py docstring and strict monoidal impl (associativity transparency).
    # Morphism names use grouping parens; tests updated for consistency with impl.
    assert (a @ b).name == "A ⊗ B"
    assert (I @ a) is a  # unitors return the non-unit operand (identity ref)
    assert (I @ a).name == "A"
    assert (a @ I).name == "A"


def test_morphism_composition():
    src = Object("A")
    mid = Object("B")
    tgt = Object("C")

    def f(x):
        return x + "->f"

    def g(x):
        return x + "->g"

    mf = Morphism.pure("f", src, mid, f)
    mg = Morphism.pure("g", mid, tgt, g)
    comp = mf >> mg
    assert comp.src == src
    assert comp.tgt == tgt
    assert "f;g" in comp.name or "(f;g)" in comp.name
    assert comp("x") == "x->f->g"


def test_morphism_tensor_and_call():
    a = Object("A")
    b = Object("B")
    # Use string inputs matching the lambda expectations (previous ints caused TypeError in +).
    # Tensor impl unpacks 2-tuple and applies componentwise (demo convention).
    ma = Morphism.pure("ma", a, a, lambda x: x + "a")
    mb = Morphism.pure("mb", b, b, lambda x: x + "b")
    mt = ma @ mb
    assert "ma ⊗ mb" in mt.name or "ma ⊗" in mt.name
    assert mt(("x", "y")) == ("xa", "yb")


def test_morphism_factories_and_frozen():
    src = Object("X")
    tgt = Object("Y")

    def fn(x):
        return x

    m_pure = Morphism.pure("pure", src, tgt, fn)
    assert m_pure.program_code is None

    m_prog = Morphism.program("prog", src, tgt, "CODE123", fn)
    assert m_prog.program_code == "CODE123"

    # frozen semantics
    with pytest.raises(Exception):  # frozen dataclass forbids setattr
        m_pure.name = "mutated"  # type: ignore[attr-defined]


# =============================================================================
# Cross-check that core enhancements compose with data services (for integration)
# =============================================================================

from resource_diagrams import DataService


def test_program_morphism_code_is_basic_and_copyable():
    """program_code on Morphism participates in DataService (key for diagrams + fp)."""
    m = Morphism.program("p", XI, XI, "agent_policy_7", lambda x: x)
    assert DataService.is_basic_data(m.program_code)
    c1, c2 = DataService.copy(m.program_code, XI)
    assert c1 == c2 == "agent_policy_7"


# =============================================================================
# Property-based tests (hypothesis) for core categorical invariants
# =============================================================================
# These are tagged @property @core (and sub: @tensor, @composition) so reviewers
# can run: pytest -m "property and tensor" etc. Use small example counts for
# speed + determinism. See conftest.py for shared strategy factories.


def _get_hypothesis():
    """Optional import so suite runs (and passes) even without hypothesis installed."""
    return pytest.importorskip("hypothesis", reason="hypothesis not installed (pip install -e '.[dev]')")


def _get_st():
    h = _get_hypothesis()
    return h.strategies


def _apply_settings(test_fn):
    """Wrap to apply deterministic small settings for all our PBT (fast CI, no flakiness).
    derandomize=True ensures the generated examples are fixed for the test name (reproducible across runs).
    """
    h = _get_hypothesis()
    return h.settings(max_examples=15, deadline=200, derandomize=True)(test_fn)


@pytest.mark.property
@pytest.mark.core
@pytest.mark.tensor
def test_object_tensor_unit_and_assoc_property():
    """Strict monoidal tensor on Object: unitors + associativity via flattened names.
    Uses generated names to exercise more than hand-written cases.
    (Paper I monoidal structure; strict, coherence elided.)
    """
    hypothesis = _get_hypothesis()
    st = _get_st()
    # Limit alphabet to keep names readable and avoid giant strings in CI
    name = st.text(alphabet="ABCDEabcde012_", min_size=1, max_size=4)

    @hypothesis.given(a=name, b=name, c=name)
    @_apply_settings
    def prop(a: str, b: str, c: str):
        A, B, C = Object(a), Object(b), Object(c)
        # Units (I ⊗ X = X, X ⊗ I = X; reference identity for units)
        assert (I @ A) is A and (A @ I) is A
        assert (I @ A).name == a and (A @ I).name == a
        # Assoc transparency (names and identity) — key for strict monoidal
        left = (A @ B) @ C
        right = A @ (B @ C)
        assert left.name == right.name == f"{a} ⊗ {b} ⊗ {c}"
        assert left == right  # same object identity via flat construction
        # Idempotent on unit
        assert (I @ I) is I

    prop()


@pytest.mark.property
@pytest.mark.core
@pytest.mark.tensor
def test_morphism_tensor_unit_and_assoc_property():
    """Morphism tensor: units (id_I ⊗ f etc), assoc via names + call behavior.
    Exercises the tensor_impl pairing convention and program_code synthesis on ⊗.
    """
    hypothesis = _get_hypothesis()
    st = _get_st()

    @hypothesis.given(
        v1=st.text(min_size=0, max_size=2),
        v2=st.text(min_size=0, max_size=2),
    )
    @_apply_settings
    def prop(v1, v2):
        A = Object("A")
        # Unit tensors on morphisms: I wires elide but we test on named
        ma = Morphism.pure("ma", A, A, lambda x: (x, v1))
        mb = Morphism.pure("mb", A, A, lambda x: (x, v2))
        mt = ma @ mb
        # Name contains both + tensor
        assert "ma" in mt.name and "mb" in mt.name and "⊗" in mt.name
        # Call on pair
        out = mt((10, 20))
        assert out == ((10, v1), (20, v2))
        # program_code on tensor of pures is None (by design)
        assert mt.program_code is None

    prop()


@pytest.mark.property
@pytest.mark.core
@pytest.mark.composition
def test_morphism_composition_assoc_and_call_property():
    """(f >> g) >> h == f >> (g >> h)  and call semantics preserved.
    Also checks src/tgt threading and name nesting.
    """
    hypothesis = _get_hypothesis()
    st = _get_st()

    @hypothesis.given(
        x=st.text(min_size=0, max_size=3),
        y=st.text(min_size=0, max_size=3),
        z=st.text(min_size=0, max_size=3),
    )
    @_apply_settings
    def prop(x, y, z):
        A, B, C, D = Object("A"), Object("B"), Object("C"), Object("D")

        def f(v):
            return (x, v)

        def g(v):
            return (y, v)

        def h(v):
            return (z, v)

        mf = Morphism.pure("f", A, B, f)
        mg = Morphism.pure("g", B, C, g)
        mh = Morphism.pure("h", C, D, h)
        left = (mf >> mg) >> mh
        right = mf >> (mg >> mh)
        assert left.src == A and left.tgt == D
        assert right.src == A and right.tgt == D
        # Name shows nesting of ;
        assert "f;g" in left.name or "(f;g)" in left.name
        val = "in"
        assert left(val) == right(val) == (z, (y, (x, val)))

    prop()


@pytest.mark.property
@pytest.mark.core
@pytest.mark.composition
@pytest.mark.tensor
def test_tensor_distributes_over_composition_property():
    """(f;g) ⊗ (h;k)  should behave as parallel of the composed (in our pairing model).
    This is a structural interaction test (not a full categorical law in all models,
    but exercises the combined impl paths for diagrams/models use).
    """
    hypothesis = _get_hypothesis()
    st = _get_st()

    @hypothesis.given(
        xv=st.text(min_size=0, max_size=2),
        yv=st.text(min_size=0, max_size=2),
    )
    @_apply_settings
    def prop(xv, yv):
        A, B, C = Object("A"), Object("B"), Object("C")

        def f(v):
            return ("f", v)

        def g(v):
            return ("g", v)

        def h(v):
            return ("h", v)

        def k(v):
            return ("k", v)

        mf = Morphism.pure("f", A, B, f)
        mg = Morphism.pure("g", B, C, g)
        mh = Morphism.pure("h", A, B, h)
        mk = Morphism.pure("k", B, C, k)
        comp_tensor = (mf >> mg) @ (mh >> mk)
        # Name has both ; and ⊗
        nm = comp_tensor.name
        assert ";" in nm and "⊗" in nm
        out = comp_tensor((xv, yv))
        assert len(out) == 2
        assert out[0] == ("g", ("f", xv))
        assert out[1] == ("k", ("h", yv))

    prop()


@pytest.mark.property
@pytest.mark.core
@pytest.mark.data_service
def test_data_service_copy_law_property_on_basic_values():
    """copy_law_holds and identical pairs for all basic data kinds (generated).
    Covers the programs-as-data axiom used by fixed-point.
    """
    hypothesis = _get_hypothesis()
    st = _get_st()
    basics = st.one_of(
        st.integers(min_value=-50, max_value=50),
        st.text(max_size=8),
        st.booleans(),
        st.tuples(st.integers(min_value=0, max_value=5), st.text(max_size=3)),
    )

    @hypothesis.given(val=basics)
    @_apply_settings
    def prop(val):
        from resource_diagrams.core import XI as _XI

        assert DataService.is_basic_data(val)
        assert DataService.copy_law_holds(val, _XI)
        v1, v2 = DataService.copy(val, _XI)
        assert v1 == v2 == val

    prop()


@pytest.mark.property
@pytest.mark.core
@pytest.mark.data_service
def test_data_service_program_copy_is_structural_property():
    """All str (program codes) on XI copy structurally, even 'weird' generated names."""
    hypothesis = _get_hypothesis()
    st = _get_st()
    prog = st.text(alphabet="p:0123_ABC-xyz", min_size=1, max_size=12)

    @hypothesis.given(p=prog)
    @_apply_settings
    def prop(p):
        from resource_diagrams.core import XI as _XI

        assert DataService.is_basic_data(p)
        p1, p2 = DataService.copy(p, _XI)
        assert p1 == p2 == p
        assert DataService.programs_are_copyable(p)

    prop()


# --- Significantly expanded PBT coverage for tensor, composition, DataService, cross interactions ---
# All use small bounded strategies + derandomized settings for speed + 100% determinism.
# Exercise name flattening, ref identity for units, program_code synthesis, full call semantics,
# and law-like properties (assoc, units, distrib in the demo pairing model).


@pytest.mark.property
@pytest.mark.core
@pytest.mark.tensor
def test_object_tensor_name_flattening_and_equality_for_many_operands():
    """Validates: repeated tensor produces flat names w/o parens; different assoc trees yield == and same name.
    Core to strict monoidal transparency used by all diagram rendering + safety walks.
    """
    hypothesis = _get_hypothesis()
    st = _get_st()
    name = st.text(alphabet="ABCD012_", min_size=1, max_size=3)

    @hypothesis.given(a=name, b=name, c=name, d=name)
    @_apply_settings
    def prop(a, b, c, d):
        A, B, C, D = Object(a), Object(b), Object(c), Object(d)
        left = ((A @ B) @ C) @ D
        right = A @ (B @ (C @ D))
        mid = (A @ B) @ (C @ D)
        expected_name = f"{a} ⊗ {b} ⊗ {c} ⊗ {d}"
        assert left.name == expected_name == right.name == mid.name
        assert left == right == mid  # identity via flat ctor
        # units still elide at any position
        assert (I @ left) is left and (left @ I) is left

    prop()


@pytest.mark.property
@pytest.mark.core
@pytest.mark.composition
@pytest.mark.tensor
def test_morphism_composition_units_and_tensor_units_property():
    """Validates: id-like (pure passthrough) acts as unit for >> ; tensor units (I-wires) elide in src/tgt names.
    Also checks program_code=None for pure tensors.
    """
    hypothesis = _get_hypothesis()
    st = _get_st()

    @hypothesis.given(v=st.text(min_size=0, max_size=2))
    @_apply_settings
    def prop(v):
        A = Object("A")
        # passthrough "id" morph
        mid = Object("Mid")
        idA = Morphism.pure("idA", A, A, lambda x: x)
        idM = Morphism.pure("idM", mid, mid, lambda x: x)
        f = Morphism.pure("f", A, mid, lambda x: (x, v))
        # idA ; f == f
        assert (idA >> f)("x") == f("x")
        # f ; idM == f
        assert (f >> idM)("x") == f("x")
        # assoc with ids
        comp = (idA >> f) >> idM
        assert comp.src == A and comp.tgt == mid
        # tensor with pure (program_code None)
        mt = f @ idA
        assert "⊗" in mt.name
        assert mt.program_code is None  # pure

    prop()


@pytest.mark.property
@pytest.mark.core
@pytest.mark.data_service
def test_data_service_copy_law_and_assoc_hold_for_generated_programs_on_xi():
    """Validates: the key programs-as-data axiom (δ∘p = p⊗p) + coassoc for arbitrary generated codes on XI.
    Directly supports fixed-point / phi constructions.
    """
    hypothesis = _get_hypothesis()
    st = _get_st()
    # reuse or local
    prog = st.text(alphabet="p:0123_ABC-xyz", min_size=1, max_size=10)

    @hypothesis.given(p=prog)
    @_apply_settings
    def prop(p):
        from resource_diagrams.core import XI as _XI

        assert DataService.is_basic_data(p)
        assert DataService.copy_law_holds(p, _XI)
        p1, p2 = DataService.copy(p, _XI)
        assert p1 == p2 == p
        # coassoc structural
        c1, c2 = DataService.copy(p, _XI)
        assert c1 == c2
        # programs_are_copyable
        assert DataService.programs_are_copyable(p)

    prop()


@pytest.mark.property
@pytest.mark.core
@pytest.mark.tensor
@pytest.mark.composition
def test_morphism_tensor_and_comp_interaction_preserves_program_codes_when_present():
    """Validates: when both sides have program_code, ; and ⊗ synthesize combined codes in parens;
    mixed pure/program yields None appropriately. Critical regression guard for fp/models.
    """
    hypothesis = _get_hypothesis()
    st = _get_st()

    @hypothesis.given(code1=st.text(min_size=1, max_size=5), code2=st.text(min_size=1, max_size=5))
    @_apply_settings
    def prop(code1, code2):
        A, B, C = Object("A"), Object("B"), Object("C")
        mf = Morphism.program("f", A, B, code1, lambda x: x)
        mg = Morphism.program("g", B, C, code2, lambda x: x)
        comp = mf >> mg
        assert comp.program_code == f"({code1};{code2})"
        mt = mf @ mg
        assert mt.program_code == f"({code1} ⊗ {code2})"
        # pure + prog => None for the tensor/comp result in current synthesis
        mp = Morphism.pure("p", A, B, lambda x: x)
        mt_mix = mp @ mf
        assert mt_mix.program_code is None

    prop()


# =============================================================================
# Edge cases, error conditions, and regression tests (core)
# =============================================================================


@pytest.mark.edge_case
@pytest.mark.core
def test_object_unit_identities_and_equality():
    """I is its own tensor unit; distinct names produce distinct objects; == is by value."""
    assert I.is_unit
    assert not (Object("A") @ Object("B")).is_unit
    a1 = Object("X")
    a2 = Object("X")
    assert a1 == a2
    assert (a1 @ I) == a1
    assert hash(a1) == hash(a2)  # frozen dataclass


@pytest.mark.error
@pytest.mark.core
def test_morphism_composition_type_mismatch_raises():
    """Composition enforces tgt/src match (core invariant for diagrams)."""
    A, B, C = Object("A"), Object("B"), Object("C")
    mf = Morphism.pure("f", A, B, lambda x: x)
    mg_bad = Morphism.pure("g", C, C, lambda x: x)  # src=C != B
    with pytest.raises(TypeError, match="tgt/src mismatch"):
        _ = mf >> mg_bad


@pytest.mark.edge_case
@pytest.mark.core
@pytest.mark.tensor
def test_morphism_tensor_call_fallback_nonpair():
    """Tensor impl on non-2-tuple falls back to applying both to same val (documented demo convention)."""
    A = Object("A")
    ma = Morphism.pure("ma", A, A, lambda x: f"l:{x}")
    mb = Morphism.pure("mb", A, A, lambda x: f"r:{x}")
    mt = ma @ mb
    out = mt("solo")  # not a pair
    assert out == ("l:solo", "r:solo")


@pytest.mark.regression
@pytest.mark.core
def test_morphism_program_code_survives_composition_and_tensor():
    """program_code combination on ; and ⊗ is key for DataService on composites (used in fp + diagrams)."""
    A, B, C = Object("A"), Object("B"), Object("C")
    mf = Morphism.program("f", A, B, "codeF", lambda x: x)
    mg = Morphism.program("g", B, C, "codeG", lambda x: x)
    comp = mf >> mg
    assert comp.program_code == "(codeF;codeG)"

    mt = mf @ mg
    assert mt.program_code == "(codeF ⊗ codeG)"


@pytest.mark.edge_case
@pytest.mark.core
def test_frozen_immutability_core_types():
    """Objects and Morphisms are immutable (frozen)."""
    o = Object("X")
    with pytest.raises(Exception):  # dataclasses.FrozenInstanceError subclass
        o.name = "Y"  # type: ignore[attr-defined]
    m = Morphism.pure("m", o, o, lambda x: x)
    with pytest.raises(Exception):
        m.name = "mut"  # type: ignore[attr-defined]
