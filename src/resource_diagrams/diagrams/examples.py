"""
Usage examples for the diagrams submodule.

These demonstrate construction of paper figures and AI modeling use-cases
(agent steps as boxes, resources as wires, programs-as-data as triangles).
Run with: python -m resource_diagrams.diagrams.examples

All examples are self-contained and use only the public diagrams API +
core types. They focus on the MVP goal: string diagram construction +
high-quality Mermaid export.
"""

from __future__ import annotations

from resource_diagrams import Morphism, Object
from resource_diagrams.diagrams import (
    MermaidRenderer,
    StringDiagram,
    box,
    from_morphism,
    seq,
    tensor,
    triangle,
    wire,
)


def example_1_paper_fixed_point() -> str:
    """Reproduce the star fixed-point construction (Paper I p.25-26) from code."""
    renderer = MermaidRenderer()
    mmd = renderer.render_fixed_point_construction("agent_policy_v1")
    print("=== Example 1: Fixed Point Construction (programmatic) ===")
    print(mmd)
    # Also build an explicit element tree version (for .to_mermaid general path)
    xi = Object("Ξ")
    p = "agent_policy_v1"
    diag = StringDiagram(
        seq(
            tensor(triangle(p, xi), wire(xi)),
            box("u", src=xi, tgt=Object("Result")),
        ),
        title="fixed_point_via_elements",
    )
    print("Explicit tree .to_mermaid() also available (general renderer):")
    print(diag.to_mermaid()[:300] + "...\n")
    return mmd


def example_2_evaluator_law_with_core() -> str:
    """Build evaluator law using core Morphism + diagrams integration."""
    Xi = Object("Ξ")
    L = Object("L")
    M = Object("M")

    def impl(x):
        return x

    # A "program" morphism (would normally come from MonoidalComputer)
    p_morph = Morphism("p_as_data", L, Xi, impl=impl, program_code="p42")
    Morphism("u^L_M", Xi, M, impl=impl)  # the evaluator box itself

    # Wrap
    p_tri = triangle("p42", Xi, encoded_morph=p_morph)

    # Simple sequential composition illustration (program + id_L into u)
    diag = StringDiagram(
        tensor(p_tri, wire(L)),  # would feed into u in full law
        title="evaluator_law_fragment",
        metadata={"paper": "Def 4.1 eq (11)"},
    )

    renderer = MermaidRenderer()
    mmd = renderer.render_evaluator_law(p_tri)
    print("=== Example 2: Evaluator Law (core + diagrams) ===")
    print(mmd)
    print("Fragment diagram repr:", repr(diag))
    return mmd


def example_3_agent_resource_model() -> str:
    """AI safety modeling: agent step (box) + resource wires + data service copy."""
    state = Object("AgentState")
    action = Object("Action")

    def step_impl(s):
        return "action"

    think = Morphism("think_step", state, action, impl=step_impl, program_code="ReAct_v3")

    # Model: copy state (data service), run two parallel reasoning steps (tensor)
    diag = StringDiagram(
        tensor(
            box("reason", src=state, tgt=action, program_code="ReAct_v3"),
            from_morphism(think).root,  # reuse
        ),
        title="agent_reasoning_with_copy",
    )

    renderer = MermaidRenderer()
    mmd_basic = renderer.render_basic_monoidal(think)
    mmd_data = renderer.render_data_service_comonoid()

    print("=== Example 3: Agent + Resource Modeling ===")
    print("Basic monoidal (agent steps):")
    print(mmd_basic[:400] + "...\n")
    print("Data service (for copying prompts/tools):")
    print(mmd_data[:300] + "...\n")
    print("Agent diagram .to_text():")
    print(diag.to_text())
    return mmd_basic


def main() -> None:
    print("Resource Diagrams — diagrams/examples.py")
    print("Demonstrating programmatic string diagram construction for paper figures + AI use.\n")
    example_1_paper_fixed_point()
    example_2_evaluator_law_with_core()
    example_3_agent_resource_model()
    print("\nAll examples complete. Mermaid output is ready for GitHub / notebooks.")


if __name__ == "__main__":
    main()
