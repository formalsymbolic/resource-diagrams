#!/usr/bin/env python3
"""
examples/info_flow_diagram.py

Demonstrates InformationChannel with explicit Δ (copy) vs ⊤ (delete)
semantics and how the resulting diagram (with annotations + safety text)
highlights leakage surfaces.

Complements the ReAct and token examples. Uses basic_info_flow_diagram
and InformationChannel from the models layer. Safety text labeled as
illustrative interpretation of geometry.

Run:
    python examples/info_flow_diagram.py

(Direct from fresh clone; guard below ensures single-command execution.)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Consistent minimal bootstrap across all promoted examples/notebooks.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams.models import (
    InformationChannel,
    basic_info_flow_diagram,
    info_flow_annotation,
)


def main() -> None:
    print("=" * 72)
    print("RESOURCE DIAGRAMS — Information Flow & Leakage Example")
    print("Using copy (Δ) vs delete (⊤) to make exfiltration paths visible")
    print("=" * 72)
    print()

    # Two channels with different semantics
    policy_chan = InformationChannel(
        "agent_policy", copyable=True, description="core instructions + tool specs"
    )
    secret_chan = InformationChannel(
        "user_credential", copyable=False, description="private fact from query"
    )

    print("Channels defined:")
    print("  ", policy_chan)
    print("  ", secret_chan)
    print()

    d = basic_info_flow_diagram(
        sensitive_channel=policy_chan,
        title="Info Flow: Policy (Δ) vs User Secret (one-way)",
    )

    print("--- Mermaid ---")
    print(d.to_mermaid())
    print()

    print("--- Generated annotations (using DataService decisions) ---")
    print(info_flow_annotation(policy_chan, "policy_text", "reasoner context"))
    print(info_flow_annotation(secret_chan, "secret-123", "observe step"))
    print()

    print("--- Safety insight ---")
    print(d.safety_explanation)
    print()

    print("=" * 72)
    print("info_flow_diagram.py complete. The fork (Δ) vs stem (⊤) distinction is annotated.")
    print("Safety text is illustrative interpretation backed by scanner.")
    print("=" * 72)


if __name__ == "__main__":
    main()
