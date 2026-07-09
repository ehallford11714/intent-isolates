"""Offline tests for span isolates + creative-burst hopper."""

from __future__ import annotations

from intentisolates import (
    CreativeBurstHopper,
    identify_span_isolates,
    typology_path_entropy,
)


SAMPLE = (
    "GOAL: I want to invent a playful metaphor. "
    "CONSTRAINT: Cannot use scare tactics. "
    "Imagine a garden with unexpected color and curious rhythm. "
    "Feel excited about the twist. "
    "Using a checklist, build a demo. "
    "OUTCOME: Result: a spark that yields delight."
)


def test_identify_span_isolates_nonempty():
    spans = identify_span_isolates(SAMPLE)
    assert len(spans) >= 3
    assert all(s.text_span.start < s.text_span.end for s in spans)
    assert any(s.protect for s in spans)


def test_creative_burst_path_length():
    spans = identify_span_isolates(SAMPLE)
    hopper = CreativeBurstHopper(spans, seed=7)
    path = hopper.burst_path(n_hops=4, mode="creative_burst")
    assert path.mode == "creative_burst"
    assert len(path.hops) == 4
    assert len(path.span_ids) == 5
    assert path.span_ids[0] == path.seed_id


def test_hop_api():
    spans = identify_span_isolates(SAMPLE)
    hopper = CreativeBurstHopper(spans, seed=3)
    h = hopper.hop(spans[0].id, mode="linear")
    assert h.from_id == spans[0].id
    assert h.to_id in hopper.by_id


def test_modes_run():
    spans = identify_span_isolates(SAMPLE)
    hopper = CreativeBurstHopper(spans, seed=11)
    for mode in ("linear", "motif_jump", "creative_burst", "random"):
        path = hopper.burst_path(n_hops=3, mode=mode)
        assert len(path.typology_path) >= 2
        assert typology_path_entropy(path.typology_path) >= 0.0


def test_entropy_known():
    assert typology_path_entropy([]) == 0.0
    assert typology_path_entropy(["goal", "goal"]) == 0.0
    assert typology_path_entropy(["goal", "constraint"]) == 1.0
