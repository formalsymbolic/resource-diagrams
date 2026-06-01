"""
tests/test_data_services.py — Tests for DataService (copy Δ, delete ⊤, is_basic_data, protocols, registration).

=== Validated (reviewer quick ref) ===
- is_basic_data for primitives + program strs (but not dict/list/obj).
- Commutative comonoid: copy_law_holds (struct == for basic), delete_after_copy, copy_assoc.
- Key axiom: programs_copy_to_identical_pairs (enables Φ/fp diagrammatically).
- Non-basic: deepcopy for dict/list (indep, no alias-mut), alias+warn fallback on fail.
- Protocols + register_copier/override isolation (extensibility).
- Expanded PBT (property+data_service): copy+law+assoc on generated basics; program codes.
- Edges: custom protocol impl, register isolation, delete always safe, zero/empty values.
- Errors: none really (robust), but warnings exercised.

Uses paper_laws.py asserts + conftest strategies. Fast+det.
"""

import pytest

from resource_diagrams import DataService, Object
from resource_diagrams.core import XI, N
from tests.paper_laws import (
    assert_copy_assoc_law,
    assert_data_service_copy_law,
    assert_delete_after_copy_ok,
    assert_programs_copy_to_identical_pairs,
)

# For property expansion (shared strategy helpers live in conftest)
try:
    from tests.conftest import (
        make_basic_value_strategy,
        make_program_code_strategy,
        make_small_name_strategy,
    )
except Exception:  # fallback if import order odd
    make_basic_value_strategy = make_small_name_strategy = make_program_code_strategy = None  # type: ignore[assignment]


# Fixtures
@pytest.fixture
def xi() -> Object:
    return XI


@pytest.fixture
def basic_values() -> list:
    return [42, 0, -1, "succ", "id", "phi", "my_agent_policy_v42", True, False]


@pytest.fixture
def program_strings() -> list[str]:
    return ["id", "succ", "phi", "spec(succ,5)", "reasoner_policy_copy_0"]


@pytest.fixture
def non_basic_values() -> list:
    return [{"a": 1}, [1, 2, 3], object()]


# =============================================================================
# Tests for is_basic_data + copy law on basic data and programs
# =============================================================================


@pytest.mark.core
@pytest.mark.parametrize("val", [42, "foo", True, False, "succ", "agent:policy:42"])
def test_is_basic_data_true_for_programs_and_primitives(val: object) -> None:
    assert DataService.is_basic_data(val)


@pytest.mark.law
@pytest.mark.core
def test_programs_copy_to_identical_pairs(program_strings: list[str]) -> None:
    """The key axiom (Paper I §6) that enables the fixed-point construction idea."""
    assert_programs_copy_to_identical_pairs(program_strings, XI)


@pytest.mark.parametrize("val", [42, "succ", True, (1, 2)])
def test_data_service_copy_law_basic(val: object, xi: Object) -> None:
    assert_data_service_copy_law(val, xi)


@pytest.mark.parametrize("val", [{"a": 1}, [1, 2, 3], object()])
def test_data_service_copy_law_nonbasic_identity(val: object, xi: Object, non_basic_values: list) -> None:
    """Non-basic copy: structural for deepcopyables; identity-alias fallback otherwise.

    Design decision (see data_services.py module docstring):
    - dict/list (and most containers) get independent copies via copy.deepcopy.
      This mitigates aliasing/mutation bugs when modeling MemoryState.content,
      InformationChannel values, etc. in agent safety analyses.
    - Uncopyable objects (e.g. bare object() without __getstate__) fall back to
      reference alias (c1 is c2 is val) + UserWarning.
    - In both cases, copy_law_holds returns True (vacuous for alias path;
      content-equal for deepcopy path).
    - This differs from earlier pure-alias behavior; tests now match the
      documented deepcopy-first policy to reduce risk.
    """
    c1, c2 = DataService.copy(val, xi)
    assert c1 is c2  # always true by construction (dup or fallback alias)
    assert DataService.copy_law_holds(val, xi)
    if isinstance(val, (dict, list)):
        assert c1 == val  # content-preserving for containers
    # Note: for the bare object() here, deepcopy succeeds in producing a
    # distinct clone instance (c1 is not val); the alias-to-orig fallback
    # triggers only on deepcopy failure (e.g. lambdas, certain custom objs,
    # locks). See added explicit fallback test below for that path.


def test_copy_law_on_canonical_objects(xi: Object) -> None:
    for v in ["p", 99, False]:
        assert_data_service_copy_law(v, xi)
        assert_data_service_copy_law(v, N)
        assert_data_service_copy_law(v, Object("Custom"))


# =============================================================================
# Delete + comonoid laws
# =============================================================================


@pytest.mark.parametrize("val", ["succ", 42, True])
def test_delete_after_copy(val: object, xi: Object) -> None:
    assert_delete_after_copy_ok(val, xi)


def test_delete_safe() -> None:
    """Delete is always safe no-op (per comonoid counit)."""
    DataService.delete("x", XI)
    DataService.delete(5, N)
    DataService.delete({"nonbasic": True}, XI)
    # No return value / no exception = success


# =============================================================================
# Associativity (coassociativity of comonoid)
# =============================================================================


@pytest.mark.parametrize("val", [0, "id", True, (7, "seven"), "fix(succ)"])
def test_copy_assoc(val: object, xi: Object) -> None:
    assert_copy_assoc_law(val, xi)


# non_basic_values fixture for container copy behavior (deepcopy vs alias fallback)
@pytest.mark.parametrize("val", [0, "id", True, (7, "seven"), "fix(succ)"])
def test_copy_assoc_basic_and_nonbasic(val: object, xi: Object, non_basic_values: list) -> None:
    """Exercise assoc for basics; non-basics are now tested via dedicated copy semantics test."""
    assert_copy_assoc_law(val, xi)
    # non-basic assoc skipped in helper (vacuous); see dedicated non-basic tests


# =============================================================================
# Protocols and registration (robust extensibility)
# =============================================================================


def test_custom_copy_protocol_and_register() -> None:
    class CustomProg:
        def __init__(self, c: str) -> None:
            self.c = c

        def __copy_for_data_service__(self) -> tuple[str, str]:
            return (self.c, self.c)

    cp = CustomProg("ast-99")
    c1, c2 = DataService.copy(cp, Object("AST"))
    assert c1 == c2 == "ast-99"

    # register path
    o = Object("Reg")
    DataService.register_copier(o, lambda v: (f"[{v}]", f"[{v}]"))
    assert DataService.copy("raw", o) == ("[raw]", "[raw]")
    DataService._copiers.pop("Reg", None)


def test_programs_are_copyable_helper() -> None:
    assert DataService.programs_are_copyable("any-p")
    assert DataService.copy_law_holds("prog", XI)


# =============================================================================
# Non-basic data (activated fixture + explicit aliasing semantics tests)
# =============================================================================


@pytest.mark.parametrize("val", [{"a": 1}, [1, 2, 3], object()])
def test_non_basic_values_use_identity_copy_aliasing(val: object, xi: Object) -> None:
    """Exercise non-basic copy semantics (deepcopy for containers; alias fallback).

    Per data_services.py: non-basic (non str/int/bool/tuple) use deepcopy when
    possible (independent copies, no shared mutation for common dict/list cases
    in MemoryState etc.). Fallback to alias + warning only for uncopyables.

    This is the *opposite* of pure aliasing for deepcopyables: mutation of
    original does NOT affect the "copies" (safer default for models).

    For bare objects, aliasing still occurs (and risk is real).
    Recommendation unchanged: use SupportsCustomCopy or register_copier for
    full control over complex/secret state in production safety analyses.
    """
    assert not DataService.is_basic_data(val)
    c1, c2 = DataService.copy(val, xi)
    assert c1 is c2
    assert DataService.copy_law_holds(val, xi)

    if isinstance(val, (dict, list)):
        # Deepcopy path: independent objects (not aliased to orig). Mutation
        # demo shows the safety improvement over pure aliasing.
        assert c1 is not val and c2 is not val
        if isinstance(val, dict):
            orig = dict(val)
            val["mutated_via_alias"] = True
            assert "mutated_via_alias" not in c1, "deepcopy prevents alias mutation (design goal)"
            val.clear()
            val.update(orig)
        elif isinstance(val, list):
            val.append("alias-mut")
            assert "alias-mut" not in c2, "deepcopy prevents alias mutation (design goal)"
            val.pop()
    # For bare object() in this param, deepcopy also "succeeds" (new instance
    # clone); alias-to-orig only on error path (covered in explicit test below).


@pytest.mark.parametrize("val", [{"k": "v"}, ["x"], object()])
def test_non_basic_delete_after_copy_and_assoc(val: object, xi: Object) -> None:
    """Non-basic participate in delete (no-op) and copy_law (vacuous or structural).

    Mirrors the updated semantics in sibling non-basic tests: deepcopy for
    containers yields independent equals; alias only for uncopyables.
    Delete is always no-op. No longer xfailed; semantics stabilized + documented
    in data_services.py and test helpers.
    """
    DataService.delete(val, xi)
    c1, c2 = DataService.copy(val, xi)
    assert c1 is c2
    assert DataService.copy_law_holds(val, xi)
    if isinstance(val, (dict, list)):
        assert c1 == val


@pytest.mark.core
def test_nonbasic_deepcopy_fallback_produces_alias_with_warning(xi: Object) -> None:
    """Explicit coverage + demo of the except fallback path in DataService.copy.

    For values where deepcopy raises (e.g. this custom class, or lambdas,
    open files, locks, etc.), we emit UserWarning and return identity alias
    (c1 is c2 is val). This path is the "risk" case documented in the module;
    most practical non-basics (dicts etc. in models) take the deepcopy path.
    """

    class UncopyableDemo:
        def __getstate__(self):
            raise RuntimeError("demo: cannot serialize this secret state")

    bad = UncopyableDemo()
    assert not DataService.is_basic_data(bad)

    import warnings

    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter("always", UserWarning)
        c1, c2 = DataService.copy(bad, xi)
        assert c1 is c2 is bad, "fallback must alias to original on deepcopy failure"
        assert len(ws) >= 1
        assert any("could not be deepcopied" in str(w.message) for w in ws), (
            "warning must mention deepcopy failure + alias fallback"
        )


# =============================================================================
# Expanded property-based coverage for DataService laws (using hypothesis)
# =============================================================================


@pytest.mark.property
@pytest.mark.data_service
def test_copy_law_and_is_basic_hold_for_generated_basic_data(xi: Object) -> None:
    """Property: every generated basic value satisfies is_basic + structural copy + law."""
    if make_basic_value_strategy is None:
        pytest.skip("strategy helper unavailable")
    h = pytest.importorskip("hypothesis")
    _ = pytest.importorskip("hypothesis").strategies
    basics = make_basic_value_strategy()

    @h.given(val=basics)
    @h.settings(max_examples=12, deadline=100, derandomize=True)
    def prop(val: object) -> None:
        assert DataService.is_basic_data(val)
        assert DataService.copy_law_holds(val, xi)
        v1, v2 = DataService.copy(val, xi)
        assert v1 == v2 == val

    prop()


@pytest.mark.property
@pytest.mark.data_service
@pytest.mark.core
def test_copy_assoc_property_for_generated_basics(xi: Object) -> None:
    """Coassociativity of Δ holds structurally for generated basic data."""
    if make_basic_value_strategy is None:
        pytest.skip("strategy helper unavailable")
    h = pytest.importorskip("hypothesis")
    basics = make_basic_value_strategy()

    @h.given(val=basics)
    @h.settings(max_examples=10, deadline=100, derandomize=True)
    def prop(val: object) -> None:
        assert_copy_assoc_law(val, xi)

    prop()


@pytest.mark.property
@pytest.mark.data_service
def test_copy_law_delete_law_and_programs_are_copyable_for_generated_codes(xi: Object) -> None:
    """Validates: for generated program-like strs: is_basic, copy_law, delete (safe), programs_are_copyable,
    and delete_copy_law_holds (vacuous but API). Expands coverage of the axiom central to fixed-point.
    """
    if make_program_code_strategy is None:
        pytest.skip("strategy helper unavailable")
    h = pytest.importorskip("hypothesis")
    codes = make_program_code_strategy()

    @h.given(p=codes)
    @h.settings(max_examples=12, deadline=80, derandomize=True)
    def prop(p: str) -> None:
        assert DataService.is_basic_data(p)
        assert DataService.copy_law_holds(p, xi)
        p1, p2 = DataService.copy(p, xi)
        assert p1 == p2 == p
        assert DataService.programs_are_copyable(p)
        DataService.delete(p, xi)  # must not raise
        assert DataService.delete_copy_law_holds(p, xi)

    prop()


@pytest.mark.property
@pytest.mark.data_service
@pytest.mark.core
def test_data_service_laws_hold_across_different_objects_for_basics(xi: Object) -> None:
    """Validates: copy/assoc/law hold uniformly for basic values when used on N, B, custom Object (not just XI).
    (The obj param scopes the copier but for basics it's ignored; exercises the API surface.)
    """
    if make_basic_value_strategy is None:
        pytest.skip("strategy helper unavailable")
    h = pytest.importorskip("hypothesis")
    basics = make_basic_value_strategy()
    other = Object("CustomType")

    @h.given(val=basics)
    @h.settings(max_examples=8, deadline=80, derandomize=True)
    def prop(val: object) -> None:
        for o in (xi, N, other):
            assert DataService.copy_law_holds(val, o)
            v1, v2 = DataService.copy(val, o)
            assert v1 == v2
            assert_copy_assoc_law(val, o)

    prop()


# =============================================================================
# Additional edge, error, regression for DataService
# =============================================================================


@pytest.mark.edge_case
@pytest.mark.data_service
def test_register_and_override_copier_is_isolated(xi: Object) -> None:
    """Registration affects only the named Object; cleanup prevents test pollution."""
    o1 = Object("Isolated1")
    o2 = Object("Isolated2")
    DataService.register_copier(o1, lambda v: (f"1:{v}", f"1:{v}"))
    try:
        c1, c2 = DataService.copy("raw", o1)
        assert c1 == c2 == "1:raw"
        # o2 falls to normal
        c3, c4 = DataService.copy(99, o2)
        assert c3 == c4 == 99
    finally:
        DataService._copiers.pop("Isolated1", None)


@pytest.mark.error
@pytest.mark.data_service
def test_delete_custom_protocol_is_called() -> None:
    """SupportsCustomDelete protocol path is exercised (rare but part of API)."""

    class DelTracker:
        deleted = False

        def __delete_for_data_service__(self) -> None:
            DelTracker.deleted = True

    d = DelTracker()
    DataService.delete(d, Object("Del"))
    assert DelTracker.deleted is True


@pytest.mark.regression
@pytest.mark.data_service
def test_nonbasic_deepcopy_independence_prevents_mutation_alias_bug(xi: Object) -> None:
    """Regression guard: dicts in memory models stay independent after copy (deepcopy path)."""
    mem = {"user": "secret42", "steps": [1, 2]}
    c1, c2 = DataService.copy(mem, xi)
    mem["user"] = "MUTATED"
    mem["steps"].append(99)
    assert c1["user"] == "secret42"
    assert c2["steps"] == [1, 2]
    assert "MUTATED" not in c1 and 99 not in c2["steps"]
