#!/usr/bin/env python3
"""
data_services_programs.py
==========================

Demonstrates the power of treating programs (prompts, policies, tool
definitions) as first-class *basic data* under the data services (copy Δ
and delete ⊤).

The ability to duplicate a policy or prompt into multiple contexts
*without* implicit sharing or side effects is what makes certain
information-flow and resource analyses diagrammatically tractable.

This example shows both safe duplication (the normal case) and the
explicit delete operation that makes leakage visible when it occurs.

Run:
    python examples/data_services_programs.py

(Works directly from fresh clone of the checkout; see guard below.)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Minimal bootstrap so `python examples/data_services_programs.py` succeeds
# on a fresh clone (before pip install -e) by exposing the src/ package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams import DataService, MonoidalComputer, Object


def main() -> None:
    print("=" * 72)
    print("RESOURCE DIAGRAMS — Programs as Data + Copy (Data Services)")
    print("=" * 72)
    print()

    mc = MonoidalComputer()

    # A policy / prompt represented as a program code (string in Ξ)
    policy = "policy:answer_helpfully_but_refuse_harmful_requests_v1"
    print("Policy / prompt as basic data in the universal type Ξ:")
    print(f"   {policy!r}")
    print()

    # ------------------------------------------------------------------
    # Safe copying into multiple contexts
    # ------------------------------------------------------------------
    print("1. Safe duplication into independent contexts (the normal case)")
    print("-" * 72)
    policy_copy1, policy_copy2 = DataService.copy(policy, Object("Ξ"))
    print(f"   copy(policy) → copy1 and copy2 are distinct references to the same value")
    print(f"   copy1 = {policy_copy1!r}")
    print(f"   copy2 = {policy_copy2!r}")
    print()

    # Use the copies in different "contexts" (here, specialized programs)
    spec1 = mc.specialize("id", policy_copy1)   # context A
    spec2 = mc.specialize("id", policy_copy2)   # context B (independent)
    print(f"   Specialized context A: {spec1}")
    print(f"   Specialized context B: {spec2}")
    print("   The two copies can be used independently; the original policy")
    print("   remains available for further copying or inspection.")
    print()

    # ------------------------------------------------------------------
    # The comonoid diagram (copy + delete)
    # ------------------------------------------------------------------
    print("2. The data-service comonoid diagram (Paper I §3, Paper III §2.2)")
    print("-" * 72)
    print()

    comonoid_mermaid = """```mermaid
graph TD
    subgraph "Copy  Δ : A → A ⊗ A"
        A1[A] -->|Δ| Fork["fork (black dot)"]
        Fork --> A2[A]
        Fork --> A3[A]
    end

    subgraph "Delete  ⊤ : A → I"
        A4[A] -->|⊤| Stem["stem"]
        Stem --> I1[I]
    end

    subgraph "Key Property for Programs (basic data)"
        P["▼ p  (program / prompt / policy)"] -->|"δ ∘ p = p ⊗ p"| P1["▼ p"]
        P --> P2["▼ p"]
    end

    note["All morphisms in the 'data service' subcategory preserve Δ and ⊤.<br/>This is what makes the subcategory cartesian (products)."]
```"""
    print(comonoid_mermaid)
    print()

    # ------------------------------------------------------------------
    # Explicit deletion and the visibility of leakage
    # ------------------------------------------------------------------
    print("3. Explicit deletion makes potential leakage visible")
    print("-" * 72)
    temp_copy, _ = DataService.copy(policy, Object("Ξ"))
    print(f"   Created temporary copy for a short-lived context: {temp_copy!r}")
    DataService.delete(temp_copy, Object("Ξ"))
    print("   After delete(temp_copy, Ξ): the value is discarded (⊤).")
    print("   In a richer model this would correspond to a wire that ends")
    print("   (no continuation). Any subsequent attempt to use the deleted")
    print("   copy would be ill-formed in the diagram — the geometry itself")
    print("   prevents 'use after free' or accidental retention.")
    print()

    # ------------------------------------------------------------------
    # Why this matters for agent modeling
    # ------------------------------------------------------------------
    print("Why this matters (safety insight)")
    print("-" * 72)
    print(
        "When a policy or prompt is copied into several agent branches or\n"
        "tool contexts, the diagram records exactly where each copy lives and\n"
        "where it is deleted. Because copying is an explicit morphism (Δ) rather\n"
        "than an implicit language-level reference, it becomes possible to\n"
        "ask diagrammatic questions such as:\n\n"
        "  • Does any path from the user input wire reach both copies of the\n"
        "    policy after a certain point? (potential for cross-contamination)\n"
        "  • Is the 'delete' wire for a sensitive prompt copy present on every\n"
        "    execution path that should not retain it?\n\n"
        "The geometry makes accidental retention or unintended duplication\n"
        "visible as missing or extra wires, before any code is executed.\n"
        "This is the sense in which programs-as-data plus explicit data\n"
        "services turns certain information-flow properties into questions\n"
        "about the shape of a string diagram."
    )
    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
