#!/usr/bin/env python3
"""
Guarded vs Unguarded one-way channel contrast as resource diagrams.

This is the canonical demonstration of the core value proposition in its
most distilled form:

- Policy and tool definitions are copyable basic data (▼ triangles that
  support explicit Δ forks).
- User secrets / private observations / credentials are modeled as one-way
  channels.
- The *only structural difference* between the two diagrams is the presence
  (guarded) or absence (unguarded) of an explicit Stem (⊤ delete) on the
  sensitive wire after first use.

The SafetyAnalyzer quantifies it: guarded diagrams show stems > 0 and
has_explicit_guards=True while the policy fork count remains identical.

This pattern is directly applicable to reviewing any agent scaffold that
mixes persistent policy/tools with transient user data (prompt injection
defense, PII handling, tool-use logging policies, etc.).

Run from a fresh clone (no install required):
    python examples/guarded_contrast.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# 3-line bootstrap for direct execution from source tree (self-contained).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resource_diagrams.models import build_guarded_vs_unguarded_contrast


def main() -> None:
    print("=" * 72)
    print("RESOURCE DIAGRAMS — Guarded vs Unguarded Contrast (core hook)")
    print("=" * 72)
    print()
    print("Policy/tool data forks via Δ in *both* versions.")
    print("The security distinction is made by one Stem (⊤) on the sensitive path.")
    print()

    contrast = build_guarded_vs_unguarded_contrast(
        sensitive_label="UserCredential",
        tool_name="web_search",
    )

    print("--- UNGUARDED (no Stem on secret) ---")
    print(contrast.unguarded.to_mermaid()[:1400])
    print("...\n")
    print("Analysis (unguarded):", contrast.analysis_unguarded)
    print()

    print("--- GUARDED (explicit Stem after use) ---")
    print(contrast.guarded.to_mermaid()[:1400])
    print("...\n")
    print("Analysis (guarded):  ", contrast.analysis_guarded)
    print()

    print("--- Quantitative contrast (structured safety geometry counts) ---")
    print(contrast.explanation)
    print()

    print("Interpretation for reviewers / red-teamers:")
    print("- Same number of policy forks (Δ) means the agent can still use")
    print("  its tools and policy across steps in both designs.")
    print("- The guarded version closes the one-way channel with a Stem.")
    print("- This is the structural pattern (in the model) that has been discussed in connection with prompt-injection and")
    print("  secret-exfiltration attacks exploit when left unguarded.")
    print()
    print("=" * 72)
    print("guarded_contrast.py complete. See models/agents.py for the builder.")
    print("=" * 72)


if __name__ == "__main__":
    main()
