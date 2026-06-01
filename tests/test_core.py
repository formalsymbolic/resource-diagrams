"""Basic tests for the core module."""

import pytest

from resource_diagrams.core import Object, Morphism


def test_object_repr():
    obj = Object("TestType")
    assert repr(obj) == "TestType"


def test_morphism_basic():
    src = Object("A")
    tgt = Object("B")
    
    def dummy_impl(x):
        return x
    
    morph = Morphism("test_morph", src, tgt, impl=dummy_impl)
    
    assert morph.name == "test_morph"
    assert morph.src == src
    assert morph.tgt == tgt
    assert "test_morph" in repr(morph)


# --- Minimal additions for rich core (frozen, tensor, composition, factories, canonicals) ---

from resource_diagrams.core import B, I, N, XI, Morphism  # reimport for new names


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
    assert (a @ b).name == "(A ⊗ B)"
    assert (I @ a) is a   # wait, returns other ref? but name
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
    ma = Morphism.pure("ma", a, a, lambda x: x + "a")
    mb = Morphism.pure("mb", b, b, lambda x: x + "b")
    mt = ma @ mb
    assert "ma ⊗ mb" in mt.name or "ma ⊗" in mt.name
    assert mt((1, 2)) == ("1a", "2b")


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
from resource_diagrams.core import XI


def test_program_morphism_code_is_basic_and_copyable():
    """program_code on Morphism participates in DataService (key for diagrams + fp)."""
    m = Morphism.program("p", XI, XI, "agent_policy_7", lambda x: x)
    assert DataService.is_basic_data(m.program_code)
    c1, c2 = DataService.copy(m.program_code, XI)
    assert c1 == c2 == "agent_policy_7"
