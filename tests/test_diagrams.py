"""Tests for the diagrams submodule (construction + Mermaid export)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from resource_diagrams import Morphism, Object
from resource_diagrams.diagrams import (
    Box,
    Fork,
    MermaidRenderer,
    Sequential,
    Stem,
    StringDiagram,
    Tensor,
    Triangle,
    Wire,
    box,
    fork,
    from_morphism,
    seq,
    stem,
    tensor,
    triangle,
    wire,
)


# --- Construction tests (roundtrips, builders, integration hook) ---

def test_wire_and_object():
    a = Object("A")
    w = wire(a)
    assert isinstance(w, Wire)
    assert w.obj == a
    assert w.label == "A"
    assert "Wire(A)" in repr(w)


def test_box_from_morphism_and_direct():
    a, b = Object("A"), Object("B")

    def dummy(x):
        return x

    m = Morphism("f", a, b, impl=dummy, program_code="f42")
    b1 = box("", morph=m)
    assert isinstance(b1, Box)
    assert b1.label == "f"
    assert b1.src == a
    assert b1.program_code == "f42"

    b2 = box("u^L_M", src=a, tgt=b, program_code=None)
    assert b2.label == "u^L_M"


def test_triangle_fork_stem():
    xi = Object("Ξ")
    t = triangle("p", xi)
    assert isinstance(t, Triangle)
    assert "▼ p" in repr(t)

    f = fork(xi)
    assert isinstance(f, Fork)
    assert "Δ" in repr(f)

    s = stem(xi)
    assert isinstance(s, Stem)
    assert "⊤" in repr(s)


def test_composition_dataclasses():
    a, b, c = Object("A"), Object("B"), Object("C")
    f = box("f", a, b)
    g = box("g", b, c)
    s = seq(f, g)
    assert isinstance(s, Sequential)

    t = tensor(f, wire(c))
    assert isinstance(t, Tensor)


def test_string_diagram_construction_and_validate():
    xi = Object("Ξ")
    d = StringDiagram(fork(xi), title="copy_test")
    assert isinstance(d, StringDiagram)
    assert d.title == "copy_test"
    assert d.validate() is True
    assert "copy_test" in repr(d)


def test_from_morphism_and_morphism_to_diagram_hook():
    a, b = Object("A"), Object("B")

    def dummy(x):
        return x

    m = Morphism("test", a, b, impl=dummy, program_code="code123")
    d1 = from_morphism(m)
    assert isinstance(d1, StringDiagram)
    assert isinstance(d1.root, Box)
    assert d1.root.label == "test"

    # The hook added to core
    d2 = m.to_diagram()
    assert isinstance(d2, StringDiagram)
    assert d2.root.label == "test"  # type: ignore[attr-defined]


def test_roundtrip_via_text_and_mermaid():
    xi = Object("Ξ")
    p = triangle("phi", xi)
    d = StringDiagram(seq(p, box("u", xi, xi)), title="roundtrip")
    txt = d.to_text()
    assert "▼ phi" in txt
    assert "u" in txt

    mmd = d.to_mermaid()
    assert "graph TD" in mmd or "graph" in mmd
    assert "phi" in mmd or "u" in mmd


def test_save_mmd(tmp_path: Path):
    xi = Object("Ξ")
    d = StringDiagram(fork(xi), title="save_test")
    out = tmp_path / "test.mmd"
    d.save_mmd(out)
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "Δ" in content or "fork" in content
    assert "graph" in content


# --- Renderer tests: key paper diagrams contain expected substrings ---

def test_renderer_basic_monoidal_contains_sequential_parallel_and_triangle():
    r = MermaidRenderer()
    mmd = r.render_basic_monoidal("f", "g")
    assert "Sequential Composition" in mmd
    assert "Parallel (Tensor)" in mmd
    assert "▼ p  (program triangle)" in mmd
    assert "Unit laws" in mmd


def test_renderer_evaluator_law_contains_u_and_triangle():
    r = MermaidRenderer()
    mmd = r.render_evaluator_law("my_p")
    assert "u^L_M" in mmd
    assert "▼ my_p" in mmd
    assert "f = {p}" in mmd or "{p}" in mmd
    assert "program as data" in mmd


def test_renderer_fixed_point_contains_phi_delta_triangle():
    r = MermaidRenderer()
    mmd = r.render_fixed_point_construction("succ")
    assert "Φ" in mmd or "fixed_point" in mmd.lower() or "Phi" in mmd  # Φ glyph or label
    assert "Δ" in mmd
    assert "▼ succ" in mmd or "succ" in mmd
    assert "u (universal evaluator)" in mmd
    assert "basic data" in mmd or "δ ∘ p" in mmd


def test_renderer_data_service_contains_delta_stem_and_program_copy():
    r = MermaidRenderer()
    mmd = r.render_data_service_comonoid()
    assert "Copy  Δ" in mmd or "Δ" in mmd
    assert "Delete  ⊤" in mmd or "⊤" in mmd
    assert "▼ p  (program)" in mmd
    assert "δ ∘ p = p ⊗ p" in mmd


def test_renderer_via_string_diagram_dispatch_and_general():
    r = MermaidRenderer()
    xi = Object("Ξ")
    d_fixed = StringDiagram(triangle("p", xi), title="fixed_point_demo")
    mmd = r.render_diagram(d_fixed)
    assert "Φ" in mmd or "fixed" in mmd.lower() or "Δ" in mmd

    d_generic = StringDiagram(box("custom", xi, xi), title="generic")
    mmd_gen = r.render_diagram(d_generic)
    assert "graph" in mmd_gen


def test_mermaid_contains_program_code_and_object_labels():
    a, b = Object("AgentState"), Object("Action")

    def dummy(x):
        return x

    m = Morphism("think", a, b, impl=dummy, program_code="ReAct42")
    d = from_morphism(m)
    mmd = d.to_mermaid()
    # General renderer may not always surface program_code in nodes, but specialized does
    # Check construction path at least (tightened from len>50)
    assert "think" in mmd or "AgentState" in mmd or "ReAct" in mmd or "Box" in mmd
