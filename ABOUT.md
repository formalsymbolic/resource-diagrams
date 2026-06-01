# Resource Diagrams

Resource Diagrams is an early experimental Python library for building and inspecting string diagrams that make explicit the distinction between copyable elements (such as policy or tool definitions) and one-way data channels in simple agent-like models.

It draws inspiration from ideas in Dusko Pavlovic’s Monoidal Computer papers, particularly the treatment of data services as commutative comonoids (Δ copy / ⊤ delete). The implementation provides basic building blocks (Object, Morphism, DataService, StringDiagram construction, Mermaid rendering) plus a small number of higher-level modeling examples.

This is a visualization and counting aid for certain structural patterns, not a rigorous formalization of the source papers and not a production security or analysis tool. The fixed-point construction, evaluators, and structural "safety" walker are simple symbolic models intended to illustrate diagrammatic ideas rather than to serve as trustworthy formal artifacts.

The project is in a very early stage: no PyPI release, minimal history on the public repository, and limited testing outside the author’s environment. It is shared in the hope that the core visualization approach may be interesting to others working on agent modeling or categorical methods, but it should be approached as alpha scaffolding.