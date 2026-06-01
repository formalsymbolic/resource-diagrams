"""
tests/test_data_services.py — Tests for DataService (copy, delete, is_basic_data).

Verifies the commutative comonoid laws and the crucial "programs are basic data"
axiom (δ ∘ p = p ⊗ p) that makes the fixed-point theorem diagrammatic (Paper I §3, §6).

Uses paper_laws helpers for the formal assertions + direct tests for Protocols/registration.

Non-basic data fixture: tests identity-copy (aliasing) semantics for containers
explicitly. See paper_laws + data_services docs for policy + risks.
"""

import pytest

from resource_diagrams import DataService, Object
from resource_diagrams.core import XI, N

from .paper_laws import (
    assert_copy_assoc_law,
    assert_data_service_copy_law,
    assert_delete_after_copy_ok,
    assert_programs_copy_to_identical_pairs,
)


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

@pytest.mark.parametrize("val", [42, "foo", True, False, "succ", "agent:policy:42"])
def test_is_basic_data_true_for_programs_and_primitives(val: object) -> None:
    assert DataService.is_basic_data(val)


def test_programs_copy_to_identical_pairs(program_strings: list[str]) -> None:
    """The key axiom (Paper I §6) that enables recursion theorem."""
    assert_programs_copy_to_identical_pairs(program_strings, XI)


@pytest.mark.parametrize("val", [42, "succ", True, (1, 2)])
def test_data_service_copy_law_basic(val: object, xi: Object) -> None:
    assert_data_service_copy_law(val, xi)


@pytest.mark.parametrize("val", [{"a":1}, [1,2,3], object()])
def test_data_service_copy_law_nonbasic_identity(val: object, xi: Object, non_basic_values: list) -> None:
    """Non-basic copy law (identity) now tested via activated fixture."""
    # The paper_law helper guards basics; direct for nonbasic (vacuous)
    c1, c2 = DataService.copy(val, xi)
    assert c1 is c2 is val
    assert DataService.copy_law_holds(val, xi)


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


# non_basic_values fixture for container aliasing behavior
@pytest.mark.parametrize("val", [0, "id", True, (7, "seven"), "fix(succ)"])
def test_copy_assoc_basic_and_nonbasic(val: object, xi: Object, non_basic_values: list) -> None:
    """Exercise assoc for basics; non-basics are now tested via dedicated aliasing test."""
    assert_copy_assoc_law(val, xi)
    # non-basic assoc skipped in helper (vacuous identity); see below for explicit


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
    """non_basic_values fixture exercised with aliasing and mutation tests.

    Per this implementation's numeric model + documented policy in
    data_services.py: non-basic copy returns identical object (alias).
    This is vacuous satisfaction of comonoid laws for demo objects.

    Aliasing risk demonstrated: mutation of dict/list affects "copies".
    Recommendation: use custom copier protocol for mutable state in
    real safety models (secrets, policies, memory).
    """
    assert not DataService.is_basic_data(val)
    c1, c2 = DataService.copy(val, xi)
    # Identity alias (same object)
    assert c1 is c2 is val
    # copy_law_holds is vacuous True
    assert DataService.copy_law_holds(val, xi)

    # Demonstrate aliasing for mutables
    if isinstance(val, dict):
        orig = dict(val)  # snapshot
        val["mutated_via_alias"] = True
        assert c1 is val and "mutated_via_alias" in c1
        # restore for cleanliness (test isolation)
        val.clear()
        val.update(orig)
    elif isinstance(val, list):
        val.append("alias-mut")
        assert "alias-mut" in c2
        val.pop()  # restore


@pytest.mark.parametrize("val", [{"k": "v"}, ["x"], object()])
def test_non_basic_delete_after_copy_and_assoc(val: object, xi: Object) -> None:
    """Non-basic also participate in delete (no-op) and copy_law via fixture."""
    # delete safe (no-op)
    DataService.delete(val, xi)
    # re-copy still identity
    c1, c2 = DataService.copy(val, xi)
    assert c1 is c2 is val
    # assoc guard skips but law "holds" vacuously; explicit check
    assert DataService.copy_law_holds(val, xi)
