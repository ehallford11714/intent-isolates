"""Tests focused on motifs and trajectories."""

from __future__ import annotations

from intentisolates import (
    Isolate,
    IsolateKind,
    TypologyLabel,
    form_motifs,
    identify_isolates,
    trajectory_from_motifs,
)
from intentisolates.types import MotifTypology


def _iso(i, label, typ, layer, start=0):
    return Isolate(
        id=f"t{i}",
        kind=IsolateKind.TEXT,
        label=label,
        typology=typ,
        confidence=0.8,
        layer=layer,
        layer_name=f"L{layer}",
        span=(start, start + len(label)),
    )


def test_typed_motif_goal_constraint_action():
    isos = [
        _iso(0, "I want success", TypologyLabel.GOAL, 3, 0),
        _iso(1, "I cannot wait", TypologyLabel.CONSTRAINT, 3, 20),
        _iso(2, "I will submit now", TypologyLabel.ACTION, 4, 40),
    ]
    motifs = form_motifs(isos)
    typed = [m for m in motifs if m.typology == MotifTypology.TYPED_PATH or str(m.typology) == "typed_path"]
    assert typed, "expected typed path motif"
    assert any("goal" in (m.pattern or "") and "action" in (m.pattern or "") for m in typed)


def test_affect_instrument_outcome_template():
    isos = [
        _iso(0, "I feel hopeful", TypologyLabel.AFFECTIVE, 1, 0),
        _iso(1, "using the toolkit", TypologyLabel.INSTRUMENTAL, 3, 20),
        _iso(2, "the outcome improves", TypologyLabel.OUTCOME, 4, 40),
    ]
    motifs = form_motifs(isos)
    assert any("affective" in (m.pattern or "") for m in motifs)


def test_trajectory_explains_layer_roles():
    text = (
        "Please review the draft. I feel unsure. "
        "I want approval. I cannot exceed the page limit. "
        "I will send it via email so that we get a decision."
    )
    isos = identify_isolates(text=text)
    motifs = form_motifs(isos)
    traj = trajectory_from_motifs(motifs, isos)
    assert "layer" in traj.summary_markdown.lower() or "Layer" in traj.summary_markdown
    assert traj.metadata.get("layer_role_note")
    assert len(traj.steps) >= 1


def test_layer_bridge_motif():
    isos = [
        _iso(0, "token surface", TypologyLabel.LEXICAL, 0, 0),
        _iso(1, "final action", TypologyLabel.ACTION, 4, 50),
    ]
    motifs = form_motifs(isos)
    bridges = [
        m for m in motifs
        if m.typology == MotifTypology.LAYER_BRIDGE or str(m.typology) == "layer_bridge"
    ]
    assert bridges
