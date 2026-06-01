# Roadmap

This document provides a high-level view of the intended direction. It is intentionally concise and is expected to evolve as the utility of particular modeling patterns and analysis techniques is better understood.

The current version provides a faithful implementation of the Paper I core together with practical AI safety modeling idioms (ReAct, resources, information flow). Features from later papers (grading and normal complexity from Paper II; coalgebraic characterizations from Paper III) remain future work. See ARCHITECTURE.md and README.md for the current state of the implementation.

## Current Focus (v0.1)

- Establish a solid, well-documented core implementation of the key structures from the Monoidal Computer papers.
- Develop initial, practical idioms for modeling common AI/agent constructs as string diagrams.
- Produce a small number of clear, worked examples that demonstrate value for analysis and security reasoning.
- Keep the project fully self-contained and usable without external services for core functionality.

## Near Term (Next Few Months)

- Expand the library of modeling patterns for agentic systems (tool use, memory, planning, multi-agent scenarios, etc.).
- Improve diagram construction and manipulation ergonomics.
- Explore (but do not ship in core) optional support for LLM-assisted diagram construction and search — any such features would live behind an explicit optional extra in a future release. (No optional extras are shipped in v0.1; the core remains fully self-contained.)
- Grow the set of worked examples, with an emphasis on security-relevant and oversight-relevant cases.
- Gather feedback from early users in the AI safety and research community.

## Longer Term (Exploratory)

- Investigate connections to existing interpretability and evaluation tooling.
- Explore exporting diagrams or fragments to proof assistants for cases where stronger guarantees are desired.
- Develop a richer catalog of diagrammatic patterns for common security and oversight concerns.
- Understand where these methods are genuinely additive versus where existing techniques are already sufficient.

## Non-Goals

Resource Diagrams is **not** trying to become:
- A general-purpose agent framework
- A fully automatic diagram synthesis tool from arbitrary code
- A replacement for existing mechanistic interpretability or evaluation libraries
- A production security auditing platform

The scope is deliberately focused on exploring the value of this particular diagrammatic approach.

## How to Read This Document

This roadmap describes direction and intent, not commitments. The most valuable contributions will likely come from discovering which modeling patterns and analysis techniques actually help people reason about real systems. The roadmap is expected to evolve based on experience with the library and feedback from early users.
