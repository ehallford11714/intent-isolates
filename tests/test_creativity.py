"""Offline tests for CreativityMeter."""

from __future__ import annotations

from intentisolates import CreativityMeter, CreativeBurstHopper, identify_span_isolates


SAMPLE = (
    "GOAL: I want to invent a playful metaphor. "
    "CONSTRAINT: Cannot use scare tactics. "
    "Imagine a garden with unexpected color and curious rhythm. "
    "Feel excited about the twist. "
    "Using a checklist, build a demo. "
    "OUTCOME: Result: a spark that yields delight."
)


def test_meter_score_path_nonempty():
    spans = identify_span_isolates(SAMPLE)
    hopper = CreativeBurstHopper.for_v2(spans, seed=7)
    path = hopper.burst_path(n_hops=4, mode="creative_burst_v2")
    report = CreativityMeter().score_burst(path, spans, motif_neighbors=hopper._motif_neighbors)
    assert 0.0 <= report.creativity_score <= 1.0
    assert 0.0 <= report.reasoning_trace_score <= 1.0
    assert report.n_spans_scored >= 2
    assert report.tradeoff_harmonic >= 0.0
    assert "weights" in report.metadata


def test_meter_score_spans():
    spans = identify_span_isolates(SAMPLE)
    report = CreativityMeter().score_spans(spans)
    assert report.fluency > 0
    assert report.n_unique_typologies >= 1


def test_v2_mode_and_multi_path():
    from intentisolates.span_burst import multi_path_burst

    spans = identify_span_isolates(SAMPLE)
    best, cands = multi_path_burst(spans, n_hops=3, k=3, seed=5, mode="creative_burst_v2")
    assert len(cands) == 3
    assert best.mode == "creative_burst_v2"
    assert "select_by" in best.metadata


def test_creative_burst_v2_in_modes():
    spans = identify_span_isolates(SAMPLE)
    hopper = CreativeBurstHopper.for_v2(spans, seed=3)
    assert "creative_burst_v2" in hopper.MODES
    path = hopper.burst_path(n_hops=3, mode="creative_burst_v2")
    assert len(path.hops) == 3
