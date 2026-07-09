"""Offline tests for identify / typology / motifs / trajectory."""

from __future__ import annotations

import json

import pytest

from intentisolates import (
    ABSTRACT_LAYERS,
    Isolate,
    IsolateKind,
    TypologyLabel,
    __version__,
    assign_layers,
    build_report,
    classify_typology,
    form_motifs,
    identify_isolates,
    trajectory_from_motifs,
)


SAMPLE = (
    "I want to finish the report. I cannot miss the deadline. "
    "I feel anxious about the review. I will submit it using the portal "
    "so that the outcome is on time."
)


def test_version():
    assert __version__ == "0.3.0"


def test_identify_text_isolates():
    isos = identify_isolates(text=SAMPLE)
    assert len(isos) >= 2
    assert all(i.kind == IsolateKind.TEXT or str(i.kind) == "text" for i in isos)
    assert all(i.layer is not None for i in isos)
    assert all(i.layer_name for i in isos)


def test_typology_goal_constraint_affect():
    g = classify_typology("I want to ship the feature")
    assert g.typology == TypologyLabel.GOAL
    assert g.confidence > 0.4

    c = classify_typology("I cannot miss the deadline")
    assert c.typology == TypologyLabel.CONSTRAINT

    a = classify_typology("I feel anxious about the review")
    assert a.typology == TypologyLabel.AFFECTIVE


def test_feature_isolates():
    feats = {"kpi_a": 0.1, "kpi_b": 0.12, "kpi_spike": 5.0, "kpi_c": 0.11}
    isos = identify_isolates(features=feats, min_feature_z=1.5)
    assert any(i.kind == IsolateKind.FEATURE or str(i.kind) == "feature" for i in isos)
    assert any(
        (i.typology == TypologyLabel.LATENT_FEATURE or str(i.typology) == "latent_feature")
        for i in isos
    )


def test_graph_orphan_isolates():
    graph = {
        "nodes": ["A", "B", "C", "orphan"],
        "edges": [["A", "B"], ["B", "C"]],
    }
    isos = identify_isolates(graph=graph)
    labels = {i.label for i in isos}
    assert "orphan" in labels
    orphan = next(i for i in isos if i.label == "orphan")
    assert orphan.typology == TypologyLabel.ORPHAN_NODE


def test_form_motifs_and_typed_path():
    isos = identify_isolates(text=SAMPLE)
    motifs = form_motifs(isos)
    assert len(motifs) >= 1
    typologies = {str(getattr(m.typology, "value", m.typology)) for m in motifs}
    # Expect at least sequence or co-occurrence; typed if cues present
    assert typologies & {"sequence", "co_occurrence", "typed_path", "chain", "layer_bridge", "triangle"}


def test_trajectory_orders_layers():
    isos = identify_isolates(text=SAMPLE)
    motifs = form_motifs(isos)
    traj = trajectory_from_motifs(motifs, isos)
    assert traj.steps
    assert traj.layer_path
    assert traj.ascii_diagram
    assert traj.mermaid.startswith("flowchart")
    assert "structural" in " ".join(traj.caveats).lower() or traj.caveats
    # Layer path should be non-decreasing in sort key sense for primary path
    keys = []
    for L in traj.layer_path:
        if isinstance(L, int):
            keys.append(L)
        else:
            keys.append(0)
    assert keys == sorted(keys)


def test_build_report_json_markdown():
    report = build_report(text=SAMPLE, include_motifs=True, include_trajectory=True)
    d = report.to_dict()
    assert d["n_isolates"] >= 1
    assert d["trajectory"] is not None
    md = report.to_markdown()
    assert "Isolate Report" in md
    assert "Reasoning Trajectory" in md
    # JSON serializable
    json.dumps(d)


def test_assign_layers_abstract():
    iso = Isolate(id="x", kind=IsolateKind.TEXT, label="hello", typology=TypologyLabel.GOAL)
    out = assign_layers([iso], strategy="abstract")
    assert out[0].layer == 3
    assert out[0].layer_name == ABSTRACT_LAYERS[3]


def test_cli_help(capsys):
    from intentisolates.cli import main

    with pytest.raises(SystemExit) as ei:
        main(["--help"])
    assert ei.value.code == 0
