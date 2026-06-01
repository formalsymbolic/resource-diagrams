# Security Policy

## Reporting a Vulnerability

If you discover a vulnerability or issue in the Resource Diagrams library itself (the core modeling primitives, diagram construction utilities, data service implementations, evaluator logic, or any supporting code), please report it responsibly.

**Preferred reporting channel**: Open a private security advisory on the GitHub repository (if the feature is enabled for the project) or contact the maintainers directly via a private channel linked from the repository.

We treat reports seriously and aim to acknowledge them promptly, investigate, and coordinate disclosure. Because the project is a research tool for analyzing the structure of other systems, clear reporting on the library's own correctness and robustness matters for the integrity of the modeling approach.

## Scope

Resource Diagrams is a library for the **analysis and modeling** of resources, information flow, and structural properties in computational systems — in particular AI and agent systems — using string diagrams grounded in monoidal category theory.

- It provides tools to construct, inspect, and reason about diagrammatic representations.
- It makes **no runtime security guarantees** of any kind.
- It does not sandbox, execute, or interpret untrusted code or models.
- It does not provide formal verification or soundness proofs for the systems being modeled.
- It is intended for research, exploratory analysis, and audit assistance only.

Vulnerabilities in the library code (e.g., incorrect modeling of a categorical construction, bugs in diagram export that could mislead analysis, or issues in the data service primitives) are in scope.

Issues in the *systems being modeled* with the library, or in external dependencies that would be used only for planned future optional augmentation/LLM features (none shipped in v0.1; the prior `openai` extra was removed as dead code), should be reported to the owners of those systems or dependencies.

Issues arising from misuse of the library (e.g., treating its output as a complete security audit) are outside the scope of library vulnerabilities.

## Supported Versions

Only the latest released version on the main branch receives security updates. Older versions are not supported.

Thank you for helping maintain the reliability of this research tooling.

This is a v0.1 research artifact intended for AI safety, formal methods, and diagrammatic modeling communities. Reports that improve the fidelity of the categorical constructions or the clarity of the safety insights are especially valued.
