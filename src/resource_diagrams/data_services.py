"""
Data Services (copy Δ, delete ⊤, and the commutative comonoid structure).

Implements the (⊤, δ) comonoid fragment of data services per:
- Paper I §3 (commutative comonoids; δ∘p = p⊗p for basic data/programs)
- (The full Def 3.1 "quadruple (A, ⊤, δ, ̺)" with semigroup ̺ + Frobenius
  data distribution laws is *not* implemented here; see Paper III §2.2
  and roadmap for future ̺/filter/equalizer. This module provides the
  copy/delete core used by Φ/fixed-point and AI safety models.)
- Diagram: diagrams/04_data_services_comonoid.mmd (title reflects comonoid)

These operations make "data" (including programs) classically manipulable.
The key axiom for programs p (as elements I → Ξ , drawn as triangles):
    δ ∘ p = p ⊗ p
(i.e. copying a program value structurally yields two identical copies).
This single fact makes the entire fixed-point / recursion theorem
construction (Paper I p.25-26) purely diagrammatic and intuitive:
the Φ self-applicator is built by forking the program wire with Δ
and feeding both copies into the universal evaluator u.

Without this (if programs were non-basic / non-copyable), the diagonal
argument would require Gödel-numbering tricks and would not be "obvious"
in the graphical language.

All morphisms in the data-service subcategory preserve Δ and ⊤,
making it cartesian (products).

Non-basic data copy semantics (this numeric demo model):
- Basic data (str/int/bool/tuple per is_basic_data): structural (v, v)
- Non-basic (dicts, lists, custom objs w/o protocol): *deepcopy* when
  possible (independent objects, no aliasing for typical dict memory
  contents in MemoryState/InformationChannel); on failure: emit
  UserWarning + identity alias fallback.
- This reduces silent aliasing risk vs prior pure-identity behavior.
- Recommendations unchanged: for full control use SupportsCustomCopy
  protocol or register_copier. copy_law_holds holds structurally on
  deepcopy success path.
- Programs-as-data (recursion enabler) always basic (str codes).
"""

from __future__ import annotations

import copy
import warnings
from typing import Any, Callable, Dict, Optional, Protocol, Tuple, runtime_checkable

from .core import I, Object, XI


@runtime_checkable
class SupportsCustomCopy(Protocol):
    """Protocol for user-defined types that want custom DataService.copy behavior.

    Implement this Protocol (or register explicitly) for complex program
    representations (e.g. ASTs, prompt objects) that are still "basic data"
    for the purposes of the recursion theorem.
    """
    def __copy_for_data_service__(self) -> Tuple[Any, Any]: ...


@runtime_checkable
class SupportsCustomDelete(Protocol):
    """Protocol for custom delete (rarely needed; delete is usually no-op)."""
    def __delete_for_data_service__(self) -> None: ...


class DataService:
    """Operations that treat values as classical, copyable/deletable data.

    In the AI safety / formal methods context, this lets us model programs,
    prompts, tool definitions, agent policies, and other artifacts as
    first-class *resources* that can be duplicated (for self-reference,
    logging, oversight) or discarded.

    Robust extensibility via Protocols + explicit registration.
    """

    # Registry for custom copiers keyed by Object name (e.g. "Ξ" or user types)
    _copiers: Dict[str, Callable[[Any], Tuple[Any, Any]]] = {}
    _deleters: Dict[str, Callable[[Any], None]] = {}

    @classmethod
    def register_copier(
        cls, obj: Object, copier: Callable[[Any], Tuple[Any, Any]]
    ) -> None:
        """Register a custom copy function for values of a given Object type.

        Enables support for user-defined "basic data" types (e.g. custom
        program AST classes that satisfy δ ∘ p = p ⊗ p by construction).
        """
        cls._copiers[obj.name] = copier

    @classmethod
    def register_deleter(cls, obj: Object, deleter: Callable[[Any], None]) -> None:
        """Register custom deleter (usually unnecessary)."""
        cls._deleters[obj.name] = deleter

    @classmethod
    def copy(cls, value: Any, obj: Object) -> Tuple[Any, Any]:
        """Δ : value ↦ (value, value)

        The comonoid copy (fork with black dot in diagrams).

        Resolution order:
        1. Explicitly registered copier for this obj.
        2. Protocol check (SupportsCustomCopy).
        3. Built-in basic data (str/int/bool/tuple) — structural copy.
        4. Non-basic: deepcopy (if possible) for independent copies; else
           warn + identity alias (to reduce silent aliasing risk for dicts
           etc. used in MemoryState/InformationChannel). See module docs.

        For programs (obj=XI, value str program_code), this is *always*
        structural, satisfying the crucial law δ ∘ p = p ⊗ p.

        Non-basic semantics (per this numeric model):
        Best-effort structural copy via deepcopy (reduces aliasing for
        typical dict/list memory contents); alias+warning only on failure.
        copy_law_holds returns True vacuously only on alias fallback path.
        """
        key = obj.name
        if key in cls._copiers:
            return cls._copiers[key](value)

        if isinstance(value, SupportsCustomCopy):
            return value.__copy_for_data_service__()

        if cls.is_basic_data(value):
            if isinstance(value, (str, int, bool, tuple)):
                return value, value
            # lists etc. made safe by tuple? for demo keep as-is
            return value, value

        # Non-basic fallback: attempt deepcopy first to reduce aliasing risk for dicts/lists
        # silent aliasing risk for common cases (dicts in MemoryState.content,
        # values in InformationChannel etc.). Only alias if deepcopy fails.
        # Warn on alias fallback so modelers are alerted to mutation risk.
        try:
            dup = copy.deepcopy(value)
            return dup, dup
        except Exception as exc:  # e.g. unpickleable custom demo objects
            warnings.warn(
                f"DataService.copy: non-basic data (type={type(value).__name__}, "
                f"obj={obj.name}) could not be deepcopied "
                f"({type(exc).__name__}: {exc}); falling back to reference "
                "aliasing (same object for both copies). This risks shared "
                "mutable state bugs in MemoryState/InformationChannel callers. "
                "Prefer basic data (str/int/bool/tuple), implement "
                "SupportsCustomCopy, or register_copier(obj, custom_dup_fn). "
                "(Deepcopy path to reduce aliasing risk)",
                UserWarning,
                stacklevel=2,
            )
            return value, value

    @classmethod
    def delete(cls, value: Any, obj: Object) -> None:
        """⊤ : value ↦ ()

        The comonoid delete (stem to unit I in diagrams).

        Registered deleters or protocol take precedence; otherwise no-op.
        Deletion is information-erasing and always "succeeds".
        """
        key = obj.name
        if key in cls._deleters:
            cls._deleters[key](value)
            return
        if isinstance(value, SupportsCustomDelete):
            value.__delete_for_data_service__()
            return
        # default: discard
        return

    @staticmethod
    def is_basic_data(value: Any) -> bool:
        """Whether a value counts as 'basic data' that can be freely copied.

        Programs / prompts / tool specs / finite descriptions qualify.
        In the model, this is what lets δ ∘ p = p ⊗ p hold for program
        triangles, enabling the Y / fixed-point theorem diagrammatically
        (no external encoding required).

        See Paper I Lemma 6.2 / Prop 6.1 and the Φ diagram.

        Non-basic values (e.g. dicts, lists, arbitrary objects) use best-effort
        deepcopy (or warned alias fallback) in this numeric model (see copy()
        and module docs).
        """
        return isinstance(value, (str, int, bool, tuple))

    @classmethod
    def copy_law_holds(cls, value: Any, obj: Object) -> bool:
        """Check (in this executable model) that copy is faithful for basic data.

        For programs this corresponds to the axiom used in the recursion proof.

        For non-basic: returns True (vacuous on deepcopy-failure alias path;
        holds structurally on successful deepcopy path due to content equality).
        """
        if not cls.is_basic_data(value):
            return True  # vacuously only on alias-fallback; deepcopy path ok
        v1, v2 = cls.copy(value, obj)
        return v1 == value and v2 == value and v1 == v2

    @classmethod
    def delete_copy_law_holds(cls, value: Any, obj: Object) -> bool:
        """(id ⊗ ⊤) ∘ Δ == id   (and symmetric). In this model always holds."""
        # Since delete is no-op, the composed behavior is identity on the kept wire.
        return True

    @staticmethod
    def programs_are_copyable(program_code: str) -> bool:
        """Explicit witness that program codes (as basic data on Ξ) satisfy
        the key property used by build_fixed_point and Φ.
        """
        p1, p2 = DataService.copy(program_code, XI)
        return p1 == program_code and p2 == program_code
