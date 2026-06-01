"""
reasoning.py — Lightweight reasoning traces, info-flow annotations, and the
core Diagram builder used by the models layer.

Trace / ProofSketch as sequences of steps.
Simple info-flow annotations that use DataService copy vs delete decisions
to highlight potential leaks (exactly the diagrammatic power of the papers).

The Diagram class is a thin ergonomic facade over the underlying string diagram
facade / compat wrapper around diagrams.StringDiagram (the single source
of truth for structure + high-quality Mermaid rendering via MermaidRenderer).
High-level builders (build_simple_react_diagram etc.) construct *real*
categorical string diagrams using fork/stem/triangle/seq/tensor/box from
the diagrams layer (with explicit Δ forks on policy/tool program triangles
for copyable basic data, stems or linear wires for one-way user secrets/queries,
tensors for parallel resources). This makes safety geometry *structural*
and the "why it matters" claims derivable from the tree (via the safety scanner
improvements).

Legacy ad-hoc element emission is deprecated (delegates for compat).
The public surface (.title, .steps, .to_mermaid(), .safety_explanation,
.to_string_diagram()) is unchanged for zero breakage of examples/notebooks/tests.

See diagrams/ for the canonical element tree + renderer (now consumed here).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from ..core import Morphism, Object
from ..data_services import DataService


# Centralized interpretive safety texts for models builders.
# These provide human-readable glosses on the *annotations and structure*
# present in the Diagram (program_code signals, copied flags, notes).
# Labeled "illustrative" to address the "hardcoded vs derived" concern
# gap. Full structural derivation from Fork/Stem nodes is a unification goal.
REACT_SAFETY_INTERPRETATION = (
    "This diagram makes visible that the tool definition (program triangle) "
    "can be copied into the context (via Δ) while the user query flows "
    "only one way (no Δ on the query wire). The policy and tool specs "
    "therefore persist and can be reflected in every subsequent memory "
    "state and observation, whereas the original user query does not "
    "automatically duplicate into tool arguments or long-term memory. "
    "This asymmetry is exactly the surface used in many prompt-injection "
    "and policy-exfiltration attacks. Token costs are annotated on "
    "parallel resource wires, showing that copied policy can drive "
    "arbitrarily expensive (or harmful) tool sequences before budget limits."
)

TOKEN_SAFETY_INTERPRETATION = (
    "Token accounting diagram makes budget depletion a visible wire. "
    "Combined with Δ on policy wires, it reveals whether dangerous "
    "copied sub-programs can execute before the budget runs out."
)

INFO_SAFETY_INTERPRETATION = (
    "Copy (Δ) on a channel creates duplication points that the diagram "
    "renders as forks. When the channel carries policy or internal state, "
    "those forks are exactly the vectors for persistence, reflection, "
    "and exfiltration. One-way (⊤) channels have no forks and therefore "
    "strictly bounded lifetime in the trace."
)


@dataclass
class Diagram:
    """Ergonomic facade over the string diagram implementation.

    This class is now a thin wrapper/facade for backward compatibility.
    The real diagram (structure + rendering) is the contained
    .string_diagram : diagrams.StringDiagram, built using the official
    primitives (fork, triangle, etc.) by the models builders. This
    unifies rendering (single MermaidRenderer source of truth) and
    makes safety geometry real and structural.

    Retained for API compat (examples, notebooks, tests continue to work
    unchanged):
    - .steps, .title, .safety_explanation, .to_mermaid(), .to_string_diagram()
    - Legacy .elements/.notes (populated for notes; main structure in .string_diagram)

    Prefer direct use of diagrams.StringDiagram + builders for new pure
    categorical work; use models.* builders for AI safety idioms (they
    return these facades or enhanced StringDiagrams).
    """

    title: str
    # The underlying diagrams.StringDiagram (the source of truth for structure and rendering).
    # Built by high-level builders using fork/triangle etc. Rendering delegates here.
    string_diagram: Optional["StringDiagram"] = None
    elements: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    steps: List[Morphism] = field(default_factory=list)
    safety_explanation: str = ""

    def add_note(self, text: str) -> None:
        self.notes.append(text)

    def add_wire(self, label: str, note: str = "") -> None:
        safe = label.replace(" ", "_").replace("[", "").replace("]", "")
        self.elements.append(f'    {safe}["{label}"]')
        if note:
            self.add_note(f"Wire {label}: {note}")

    def add_triangle(self, label: str, content: str) -> None:
        """Program / policy triangle (▼) — always copyable basic data."""
        safe = label.replace(" ", "_")
        # Use HTML-ish label to evoke the paper triangle glyph
        self.elements.append(f'    {safe}["▼ {content}"]')
        self.elements.append(f"    style {safe} fill:#fff3e0,stroke:#e65100,stroke-width:2px")
        self.add_note(f"Triangle {label}: {content} (program data, Δ-copyable per DataService)")

    def add_box(self, name: str, desc: str, style: str = "default") -> None:
        safe = name.replace(" ", "_").replace("[", "").replace("]", "")
        self.elements.append(f'    {safe}["{desc}"]')
        if style == "resource":
            self.elements.append(f"    style {safe} fill:#e3f2fd,stroke:#1565c0")
        elif style == "step":
            self.elements.append(f"    style {safe} fill:#f3e5f5,stroke:#7b1fa2")
        self.add_note(f"Box {name}: {desc}")

    def add_morphism_step(
        self,
        morph: Morphism,
        copied_policy: bool = False,
        cost: Optional[int] = None,
    ) -> None:
        """Add a core Morphism as a box, with AI-specific annotations."""
        self.steps.append(morph)
        extra = ""
        if copied_policy:
            extra = " [Δ copied policy/tool]"
        if cost:
            extra += f" [cost:{cost}]"
        desc = f"{morph.name}{extra}"
        style = "step"
        self.add_box(morph.name, desc, style=style)
        if copied_policy:
            self.add_note(
                f"Step {morph.name}: policy/tool data was duplicated (Δ) into this step. "
                "This is the source of persistence/leakage surfaces."
            )
        if cost:
            self.add_note(f"Step {morph.name} consumes {cost} tokens on resource wire.")

    def add_resource_consumption(
        self,
        resource_wire: str,
        from_obj: Object,
        to_obj: Object,
        amount: int,
        step_name: str,
    ) -> None:
        """Annotate consumption along a parallel resource wire."""
        safe_wire = resource_wire.replace(" ", "_")
        safe_from = str(from_obj).replace(" ", "_").replace("[", "").replace("]", "")
        safe_to = str(to_obj).replace(" ", "_").replace("[", "").replace("]", "")
        self.elements.append(f"    {safe_from} -->|{amount} tokens| {safe_to}")
        self.elements.append(f"    style {safe_from} fill:#fff8e1,stroke:#f57f17")
        self.add_note(
            f"Resource {resource_wire}: {from_obj} --{amount}--> {to_obj} at {step_name}"
        )

    def add_flow(self, src: str, tgt: str, label: str = "") -> None:
        s = src.replace(" ", "_").replace("[", "").replace("]", "")
        t = tgt.replace(" ", "_").replace("[", "").replace("]", "")
        if label:
            self.elements.append(f"    {s} -->|{label}| {t}")
        else:
            self.elements.append(f"    {s} --> {t}")

    def to_mermaid(self) -> str:
        """Emit complete, renderable Mermaid source.

        If .string_diagram is present (for builders that use the diagrams layer)
        output), delegates to it (the official diagrams.MermaidRenderer,
        now with real Fork/Stem/Triangle geometry for safety properties).
        Legacy ad-hoc emission retained only for pure-legacy Diagram()
        constructions (deprecated path).
        """
        if self.string_diagram is not None:
            # Consume the real diagrams layer for rendering (unification).
            base = self.string_diagram.to_mermaid()
            # Append any additional model notes if the structural diagram didn't already include them.
            if self.notes:
                note_block = "\n    subgraph AdditionalNotes\n"
                for i, n in enumerate(self.notes[:3]):
                    safe = n[:70].replace('"', "'")
                    note_block += f'        noteA{i}["{safe}"]\n'
                note_block += "    end\n"
                base += note_block
            return base

        # Legacy fallback (ad-hoc; deprecated after unification; used only if
        # Diagram constructed manually without string_diagram).
        lines: List[str] = []
        lines.append(f"%% {self.title}")
        lines.append("%% Resource Diagram — generated by resource_diagrams.models")
        lines.append("%% Wires = data or resource channels; boxes = steps; ▼ = copyable program/policy data")
        lines.append("graph TD")
        lines.append("    direction TB")

        # Emit collected elements (wires, boxes, triangles, flows)
        for el in self.elements:
            lines.append("    " + el if not el.strip().startswith("style") else el)

        # Emit notes as a side subgraph for readability
        if self.notes:
            lines.append("")
            lines.append("    subgraph Notes")
            lines.append("        direction TB")
            for i, note in enumerate(self.notes[:8]):  # cap for cleanliness
                safe_n = f"note_{i}"
                # Escape special chars lightly for mermaid
                ntext = note.replace('"', "'")[:120]
                lines.append(f'        {safe_n}["{ntext}"]')
            lines.append("    end")

        # Legend
        lines.append("")
        lines.append("    subgraph Legend")
        lines.append('        L1["▼ = program/policy (Δ-copyable basic data)"]')
        lines.append('        L2["Box = computation / agent step (with cost)"]')
        lines.append('        L3["Arrow = wire (data or resource flow)"]')
        lines.append('        L4["No fork on wire = one-way / delete-after-use (⊤)"]')
        lines.append("    end")
        lines.append("    style L1 fill:#fff3e0,stroke:#e65100")
        lines.append("    style L3 fill:#e3f2fd")

        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_mermaid()

    def __repr__(self) -> str:
        return f"Diagram({self.title!r}, {len(self.steps)} steps)"

    def _scan_safety_geometry(self) -> dict[str, Any]:
        """Lightweight structural scanner that walks the (trace) diagram data
        for presence of signals proxying Δ forks on policy wires vs one-way
        linear query/obs wires.

        Inspects:
        - .steps[].program_code (non-None on policy/tool steps = Δ-copyable basic data)
        - step names for observe/query patterns (one-way)
        - elements/notes for ▼ triangles, Δ mentions, resource arrows

        This provides a *derived* basis for safety texts (vs pure hardcoded),
        making the "geometry makes visible" claim more accurate for the
        lightweight models layer. Full categorical Fork/Stem walk awaits
        unification with diagrams/ layer (see to_string_diagram bridge).

        Returns counts/flags suitable for prefixing explanations.
        """
        steps = self.steps or []
        elements = self.elements or []
        notes = self.notes or []

        policy_copy_signals = 0
        oneway_signals = 0
        resource_wires = 0

        for s in steps:
            pc = getattr(s, "program_code", None)
            name_l = getattr(s, "name", str(s)).lower()
            if pc and any(
                k in (pc or "").lower() for k in ("policy", "tool_def", "reasoner", "compute")
            ):
                policy_copy_signals += 1
            elif pc is None and any(k in name_l for k in ("observe", "query", "oneway", "secret")):
                oneway_signals += 1

        for el in elements:
            el_l = el.lower()
            if "token" in el_l or ("-->" in el and "token" in el_l):
                resource_wires += 1
            if "▼" in el or "policy" in el_l:
                policy_copy_signals += 1  # heuristic boost from triangle notes

        for n in notes:
            n_l = n.lower()
            if "Δ" in n or "copy" in n_l or "fork" in n_l:
                policy_copy_signals += 1
            if "one-way" in n_l or "one way" in n_l or "delete" in n_l:
                oneway_signals += 1

        has_policy_triangle = any(
            "▼" in e or "policy" in e.lower() or "triangle" in e.lower() for e in elements
        )

        return {
            "policy_copy_steps": policy_copy_signals,
            "oneway_steps": oneway_signals,
            "has_resource_wires": resource_wires > 0 or any("budget" in e.lower() for e in elements),
            "has_policy_triangle": has_policy_triangle,
        }

    def get_safety_explanation(self) -> str:
        """Return the safety_explanation clearly labeled as interpretive of
        the (annotated) geometry, optionally incorporating a scan-derived prefix.
        """
        scan = self._scan_safety_geometry()
        prefix = (
            "Illustrative interpretation of the shown geometry "
            f"(scanner: {scan['policy_copy_steps']} policy/tool Δ-copy signals via program_code/annotations, "
            f"{scan['oneway_steps']} one-way steps, "
            f"resource wires present: {scan['has_resource_wires']}, "
            f"policy triangles: {scan['has_policy_triangle']}): "
        )
        base = self.safety_explanation or (
            "No safety explanation was recorded. The underlying Morphism steps "
            "and annotations (program_code presence = Δ proxy; None = one-way) "
            "surface the copy vs linear flow distinction for analysis."
        )
        # Avoid double-prefixing
        if base.startswith("Illustrative interpretation") or base.startswith("This diagram"):
            return base
        return prefix + base

    def to_string_diagram(self) -> Optional["StringDiagram"]:
        """Return the underlying diagrams.StringDiagram.

        Post-unification, builders construct the .string_diagram using the
        official fork/triangle/seq etc primitives, so this returns a rich
        tree with actual geometry (Δ forks on policy etc). The old seq-chaining
        logic is legacy fallback only.

        Attaches safety_explanation to metadata for roundtrips.
        """
        if self.string_diagram is not None:
            sd = self.string_diagram
            if hasattr(sd, "metadata") and isinstance(sd.metadata, dict):
                if self.safety_explanation and "safety_explanation" not in sd.metadata:
                    sd.metadata["safety_explanation"] = self.get_safety_explanation()
            return sd

        # Legacy fallback (pre-unification or manual Diagram() construction)
        try:
            from ..diagrams import (
                StringDiagram,
                box,
                from_morphism,
                seq,
            )

            if not self.steps:
                sd = StringDiagram(box(self.title), title=self.title)
                if hasattr(sd, "metadata") and isinstance(sd.metadata, dict):
                    sd.metadata["safety_explanation"] = self.get_safety_explanation()
                return sd

            # Chain sequentially (traces are linear by design in models)
            current: Any = from_morphism(self.steps[0]).root
            for morph in self.steps[1:]:
                current = seq(current, from_morphism(morph).root)

            sd = StringDiagram(current, title=self.title)
            # Attach models-specific info for roundtrip/audit (if metadata present)
            if hasattr(sd, "metadata") and isinstance(getattr(sd, "metadata", None), dict):
                sd.metadata["models_safety_explanation"] = self.get_safety_explanation()
                sd.metadata["models_scan"] = self._scan_safety_geometry()
                sd.metadata["models_bridge_note"] = (
                    "Converted from models.Diagram; full forks/stems not present "
                    "(lightweight annotations used for safety text)"
                )
            return sd
        except Exception:
            # graceful: lightweight .to_mermaid() + .get_safety_explanation() remain primary
            return None


def info_flow_annotation(
    channel: "InformationChannel",  # forward ref ok, or import inside
    value: Any,
    context: str = "",
) -> str:
    """Return a human-readable annotation for a copy/delete decision.

    Used by traces to surface leakage risk.
    """
    from .resources import InformationChannel as IC  # avoid top-level circular if any

    if isinstance(channel, IC):
        if channel.copyable:
            v1, v2 = channel.apply_copy(value)
            return (
                f"INFO-FLOW: {channel.name} copied (Δ) in {context}. "
                f"Value now present in two places. Leakage risk: {channel.description or 'high if sensitive'}."
            )
        else:
            channel.apply_delete(value)
            return (
                f"INFO-FLOW: {channel.name} deleted (⊤) after use in {context}. "
                "Linear flow; reduced persistence."
            )
    return f"INFO-FLOW on {channel}: unknown semantics"


def basic_info_flow_diagram(
    sensitive_channel: Optional["InformationChannel"] = None,
    title: Optional[str] = None,
) -> Diagram:
    """Worked example: simple info-flow diagram highlighting copy vs delete.

    If no channel supplied, creates a default "internal_thoughts" (copyable)
    and a "user_secret" (one-way).

    Demonstrates the diagrammatic distinction that makes certain
    exfiltration paths obvious.
    """
    if title is None:
        title = "Info-Flow Example: Copy vs One-Way Channels"

    from .resources import InformationChannel as IC

    d = Diagram(title=title)

    if sensitive_channel is None:
        sensitive_channel = IC("internal_thoughts", copyable=True, description="agent scratchpad")

    # Always create a one-way contrast channel for the diagram's observe demo
    # (independent of caller-supplied sensitive_channel; avoids UnboundLocalError
    # and makes the "copy vs one-way" demo self-contained in all call modes).
    one_way = IC("user_private_fact", copyable=False, description="PII or credential")

    d.add_triangle("policy", "▼ Agent policy (always Δ)")
    d.add_wire("query", "UserQuery (one-way)")

    # Show a reason step that *copies* the sensitive channel
    reason = Morphism(
        "ReasonWithCopy",
        Object("Context"),
        Object("Context+Leak"),
        impl=lambda x: x,
        program_code="reasoner",
    )
    d.add_morphism_step(reason, copied_policy=True)

    # Annotation using the channel
    ann = info_flow_annotation(sensitive_channel, {"secret": "foo"}, context="reason step")
    d.add_note(ann)

    # Contrast: a one-way observation
    obs = Morphism(
        "ObserveOneWay",
        Object("Result"),
        Object("Memory"),
        impl=lambda x: x,
        program_code=None,
    )
    d.add_morphism_step(obs, copied_policy=False)
    ann2 = info_flow_annotation(one_way, "secret-value-xyz", context="observe")
    d.add_note(ann2)

    d.add_note(
        "Safety insight: The Δ fork on the sensitive channel means the same "
        "value can reach tool arguments and be echoed in future cycles. "
        "The one-way channel has no fork — it is deleted after the "
        "observe step and cannot be re-used or leaked via copying."
    )
    # Use the centralized safety interpretation text.
    d.safety_explanation = (
        "Illustrative interpretation of the shown geometry (copyable vs one-way channel annotations): "
        + INFO_SAFETY_INTERPRETATION
    )
    return d


@dataclass
class ReasoningTrace:
    """A sequence of reasoning steps with associated diagram and resource annotations.

    This is the primary high-level artifact for modeling multi-step agent
    behavior in a way that makes information-flow and resource properties
    inspectable (the core value proposition of the diagrammatic approach).
    """

    title: str
    steps: List[Morphism] = field(default_factory=list)
    diagram: Optional[Diagram] = None
    total_cost: int = 0
    notes: List[str] = field(default_factory=list)

    def add_step(self, morph: Morphism, cost: int = 0, copied: bool = False) -> None:
        self.steps.append(morph)
        self.total_cost += cost
        if self.diagram:
            self.diagram.add_morphism_step(morph, copied_policy=copied, cost=cost if cost else None)

    def to_mermaid(self) -> str:
        if self.diagram:
            return self.diagram.to_mermaid()
        d = Diagram(title=self.title)
        for s in self.steps:
            d.add_morphism_step(s)
        return d.to_mermaid()

    def __repr__(self) -> str:
        return f"ReasoningTrace({self.title!r}, {len(self.steps)} steps, cost={self.total_cost})"
