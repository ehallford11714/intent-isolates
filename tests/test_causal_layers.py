"""Offline tests for layer causal / IV bridge."""

from __future__ import annotations

import json

import pytest

from intentisolates import __version__, identify_isolates, form_motifs
from intentisolates.causal import (
    LayerCausalSuite,
    build_feature_frame,
    estimate_indication,
    estimate_layer_iv,
)


SAMPLE = (
    "I want to finish the report. I cannot miss the deadline. "
    "I feel anxious about the review. I will submit it using the portal "
    "so that the outcome is on time."
)


def test_version_bumped():
    assert __version__ == "0.3.0"


def test_feature_frame_columns():
    isos = identify_isolates(text=SAMPLE)
    motifs = form_motifs(isos)
    table = build_feature_frame(isos, motifs, outcome_hint="on time", n_bootstrap=24, seed=3)
    assert table.rows
    assert table.outcome_column == "Y"
    assert "Y" in table.columns
    assert any(c.startswith("isolate_") for c in table.columns)
    assert len(table.rows) == 24
    d = table.to_dict()
    assert d["n_rows"] == 24


def test_indication_and_mock_iv():
    isos = identify_isolates(text=SAMPLE)
    motifs = form_motifs(isos)
    table = build_feature_frame(isos, motifs, outcome_hint="decision", n_bootstrap=40, seed=11)
    ind = estimate_indication(table, min_abs=0.01)
    assert isinstance(ind, list)
    edges, notes = estimate_layer_iv(table, mock=True)
    assert notes
    assert edges  # mock should always produce at least one when Z/X exist
    e = edges[0]
    assert e.kind == "causation"
    assert e.instrument
    assert e.source
    assert e.method == "mock_iv"


def test_stdlib_iv_path():
    """Without forcing mock, stdlib Wald IV should still return or note skip."""
    isos = identify_isolates(text=SAMPLE)
    motifs = form_motifs(isos)
    table = build_feature_frame(isos, motifs, n_bootstrap=48, seed=7)
    edges, notes = estimate_layer_iv(table, mock=False)
    assert isinstance(edges, list)
    assert notes
    # Prefer real edges when design is identified
    if edges:
        assert edges[0].method in {
            "causaliv",
            "autocausal_numpy_2sls",
            "stdlib_wald_iv",
        }
        assert edges[0].target == "Y"


def test_layer_causal_suite_report():
    suite = LayerCausalSuite.from_text(SAMPLE)
    result = suite.run(outcome_hint="on time", n_bootstrap=32, seed=5, mock_iv=True)
    assert result.isolates
    assert result.motifs
    assert result.trajectory is not None
    assert result.feature_table is not None
    md = result.to_markdown()
    assert "Indication matrix" in md
    assert "Causation (IV edges)" in md
    assert "Caveats" in md
    payload = result.to_dict()
    json.dumps(payload)  # serializable
    assert payload["n_isolates"] >= 1


def test_cli_causal(capsys):
    from intentisolates.cli import main

    code = main(
        [
            "causal",
            "--text",
            SAMPLE,
            "--outcome-hint",
            "on time",
            "--mock-iv",
            "--format",
            "json",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "causation_edges" in data
    assert "indications" in data
