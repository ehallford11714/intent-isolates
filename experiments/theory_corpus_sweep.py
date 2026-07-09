#!/usr/bin/env python3
"""Unified theory-corpus offline sweep — adjudicate cognition / burst / causal claims.

Loads diverse fixtures, runs a condition grid spanning dual-process, WM/compact,
GWT multipath, precision (anchor_pull), motif vs burst, incubation, layer planning,
and soft LayerCausal IV when available.

Usage (from IntentIsolates repo root)::

    python experiments/theory_corpus_sweep.py
    python experiments/theory_corpus_sweep.py --seeds 5 --hops 5
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from intentisolates import (  # noqa: E402
    CreativeBurstHopper,
    CreativityMeter,
    identify_span_isolates,
)
from intentisolates.span_burst import (  # noqa: E402
    filter_spans_for_burst,
    layer_path_monotonicity,
    multi_path_burst,
    typology_path_entropy,
)

try:
    from intentisolates.orchestration import orchestration_meta
except ImportError:
    def orchestration_meta(**kwargs: Any) -> dict[str, Any]:  # type: ignore
        return dict(kwargs)

# ---------------------------------------------------------------------------
# Fixtures (8 diverse)
# ---------------------------------------------------------------------------
FIXTURES: list[dict[str, Any]] = [
    {
        "id": "product_metaphor",
        "kind": "creative",
        "text": (
            "GOAL: I want to invent a playful onboarding metaphor for a budgeting app. "
            "CONSTRAINT: Cannot mention debt shaming or scare tactics. "
            "Imagine a garden where each sprout is a savings habit with unexpected color. "
            "Feel curious about the texture of small wins stacking into a canopy. "
            "Using a weekly check-in ritual via gentle reminders, build a rhythm. "
            "Do not exceed a 30-second first-run demo. "
            "OUTCOME: Result: a metaphor kit that sparks delight without pressure."
        ),
    },
    {
        "id": "story_twist",
        "kind": "creative",
        "text": (
            "My goal is to draft a short story opening with a wild twist. "
            "Constraint: must not reveal the antagonist in the first paragraph. "
            "The hallway smelled like rain and old paper; a curious rhythm tapped the pipes. "
            "I feel excited and a little afraid of the dream that won't stay put. "
            "Using a notebook and a timer, write three false leads. "
            "Require that every clue also works as a metaphor. "
            "Outcome: therefore the opening yields a burst of questions, not answers."
        ),
    },
    {
        "id": "research_creative",
        "kind": "planning",
        "text": (
            "Aim to produce a literature summary on prompt compression with a creative angle. "
            "Limit the draft to 800 words. Must cite LLMLingua and dictionary-encoding work. "
            "Cannot claim LLM task equivalence without a citation. "
            "Imagine compression as origami: folds that preserve the crease of intent. "
            "Feel frustrated by lossy drops that erase constraints mid-trace. "
            "Create an outline through thematic clustering, then write. "
            "Outcome: draft produced under the word limit; yields a citable playful summary."
        ),
    },
    {
        "id": "brand_voice",
        "kind": "constraint_heavy",
        "text": (
            "Objective: refresh brand voice for a climate toolkit. "
            "Constraint: require hopeful tone; must not use doom language. "
            "Budget for the campaign window is two weeks. "
            "Spark ideas with textures of wind, tide, and shared tables. "
            "I want neighbors to feel invited, not lectured. "
            "Deploy a playful checklist via community workshops. "
            "Result: consequently the voice guide leads to warmer outreach copy."
        ),
    },
    {
        "id": "deploy_plan",
        "kind": "planning",
        "text": (
            "GOAL: ship the API migration without downtime. "
            "CONSTRAINT: must keep read replicas available; cannot drop traffic during peak. "
            "First instrument health checks via canary. "
            "Feel anxious about rollback windows under two hours. "
            "Action: roll forward using blue-green, then verify latency. "
            "Do not skip the schema backfill step. "
            "OUTCOME: therefore the cutover yields zero failed requests."
        ),
    },
    {
        "id": "tool_log_repetitive",
        "kind": "tool_log",
        "text": (
            "GOAL: finish the incident review. CONSTRAINT: preserve PII redaction rules. "
            "TOOL_LOG: retry=1 ok=true. TOOL_LOG: retry=2 ok=true. "
            "TOOL_LOG: retry=3 ok=true. TOOL_LOG: retry=4 ok=true. "
            "noise filler line repeated again and again without new facts. "
            "ACTION: open the postmortem template using the incident id. "
            "CONSTRAINT mid: cannot paste raw customer emails into the draft. "
            "OUTCOME: the review yields a timeline with root cause tagged."
        ),
    },
    {
        "id": "causal_narrative",
        "kind": "causal",
        "text": (
            "GOAL: estimate whether reminder intensity affects on-time filing. "
            "Early lexical cue: weather was mild; incidental mood was calm. "
            "INSTRUMENT candidate: random assignment to soft vs loud reminder channel. "
            "Mid latent: perceived urgency mediates attention to the deadline. "
            "CONSTRAINT: cannot claim causation from association alone. "
            "ACTION: compare filing rates after instrumenting channel assignment. "
            "OUTCOME: therefore beta_IV may show a causal lift if first-stage is strong."
        ),
    },
    {
        "id": "constraint_stack",
        "kind": "constraint_heavy",
        "text": (
            "I want to export analytics without violating privacy. "
            "Must anonymize identifiers. Cannot include free-text notes. "
            "Budget constraint: finish before Friday. "
            "Require audit log retention for ninety days. "
            "Using hashing via salted tokens, transform the export. "
            "Do not leave raw SSNs in staging. "
            "Result: consequently the package yields a compliant download."
        ),
    },
]

# Theory claim registry (enumeration)
CLAIMS: list[dict[str, Any]] = [
    {"id": "P1", "pred": "H(v2)>H(random); C(v2) within 0.05 of C(random)", "conds": ("creative_burst_v2", "random")},
    {"id": "P2", "pred": "anchor_R(v2)>anchor_R(random)", "conds": ("creative_burst_v2", "random")},
    {"id": "P3", "pred": "layer_mono(layer_cot)>=layer_mono(divergent)", "conds": ("layer_cot", "divergent_guilford")},
    {"id": "P4", "pred": "C(div)>C(conv); entropy(div)>=entropy(conv)", "conds": ("divergent_guilford", "convergent_constrained")},
    {"id": "P5", "pred": "H(multipath_H)>=H(v2)", "conds": ("multipath_k5_H", "creative_burst_v2")},
    {"id": "P6", "pred": "protect_hotset R/anchor_R >= truncate_drop", "conds": ("wm_protect_hotset", "wm_truncate_drop")},
    {"id": "P7", "pred": "conflict_schedule H>=fixed schedule v2", "conds": ("conflict_schedule_2", "creative_burst_v2")},
    {"id": "P8", "pred": "high side_hop raises C without large R loss vs convergent", "conds": ("insight_sidehop", "convergent_constrained")},
    {"id": "L1", "pred": "motif_jump R > v2 R; motif C < v2 C", "conds": ("motif_jump", "creative_burst_v2")},
    {"id": "L2", "pred": "v2 R > v1 R", "conds": ("creative_burst_v2", "creative_burst_v1")},
    {"id": "L3", "pred": "divergent entropy >= convergent", "conds": ("divergent_guilford", "convergent_constrained")},
    {"id": "L4", "pred": "convergent anchor_R >= divergent", "conds": ("convergent_constrained", "divergent_guilford")},
    {"id": "G1", "pred": "multipath select-by-H >= select-by-C on R", "conds": ("multipath_k5_H", "multipath_k5_C")},
    {"id": "G2", "pred": "multipath k=5 H >= k=3 H", "conds": ("multipath_k5_H", "multipath_k3_H")},
    {"id": "G3", "pred": "multipath k=7 H >= k=5 H (weak)", "conds": ("multipath_k7_H", "multipath_k5_H")},
    {"id": "PP1", "pred": "high_precision (anchor_pull) R >= low_precision", "conds": ("precision_high", "precision_low")},
    {"id": "PP2", "pred": "low_precision C >= high_precision C", "conds": ("precision_low", "precision_high")},
    {"id": "I1", "pred": "incubation H >= pure divergent H", "conds": ("incubation_alt", "divergent_guilford")},
    {"id": "I2", "pred": "two_phase H >= v2 H", "conds": ("two_phase", "creative_burst_v2")},
    {"id": "PL1", "pred": "layer_cot H >= divergent H", "conds": ("layer_cot", "divergent_guilford")},
    {"id": "B1", "pred": "burst_Z first_stage_F >= random_Z (causal)", "conds": ("causal_burst_z", "causal_random_z")},
    {"id": "B2", "pred": "high-R path causation_overlap >= indication_only pattern", "conds": ("convergent_constrained", "divergent_guilford")},
    {"id": "B4", "pred": "multipath_H then edges >= random path edges", "conds": ("multipath_k5_H", "random")},
    {"id": "S1", "pred": "v2 H >= linear H", "conds": ("creative_burst_v2", "linear")},
    {"id": "S2", "pred": "creative_burst_v1 entropy >= linear", "conds": ("creative_burst_v1", "linear")},
    {"id": "S3", "pred": "motif_jump mono >= divergent mono", "conds": ("motif_jump", "divergent_guilford")},
]


def _conditions() -> list[dict[str, Any]]:
    return [
        {"id": "linear", "mode": "linear", "knobs": {}, "theory": ["S1"]},
        {"id": "random", "mode": "random", "knobs": {}, "theory": ["P1", "P2"]},
        {"id": "motif_jump", "mode": "motif_jump", "knobs": {}, "theory": ["L1", "S3"]},
        {"id": "creative_burst_v1", "mode": "creative_burst", "knobs": {"anchor_pull": 0.55}, "theory": ["L2", "S2"]},
        {
            "id": "divergent_guilford",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {
                "novelty_weight": 1.6,
                "anchor_pull": 0.25,
                "anchor_schedule": 0,
                "layer_bias": 0.15,
                "motif_weight": 0.20,
                "side_hop_prob": 0.35,
            },
            "theory": ["P3", "P4", "L3", "L4", "I1", "PL1"],
        },
        {
            "id": "convergent_constrained",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {
                "novelty_weight": 0.6,
                "anchor_pull": 1.0,
                "anchor_schedule": 2,
                "layer_bias": 0.45,
                "motif_weight": 0.50,
                "side_hop_prob": 0.05,
            },
            "theory": ["P4", "L4", "P8", "B2"],
        },
        {
            "id": "layer_cot",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {
                "novelty_weight": 0.9,
                "anchor_pull": 0.65,
                "anchor_schedule": 3,
                "layer_bias": 0.95,
                "motif_weight": 0.40,
                "side_hop_prob": 0.08,
            },
            "theory": ["P3", "PL1"],
        },
        {
            "id": "creative_burst_v2",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {},
            "theory": ["P1", "P2", "L2", "S1", "P5", "I2"],
        },
        {
            "id": "precision_high",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {"anchor_pull": 1.15, "anchor_schedule": 2, "novelty_weight": 0.85},
            "theory": ["PP1", "PP2"],
        },
        {
            "id": "precision_low",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {"anchor_pull": 0.20, "anchor_schedule": 0, "novelty_weight": 1.45, "side_hop_prob": 0.30},
            "theory": ["PP1", "PP2"],
        },
        {
            "id": "insight_sidehop",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {"side_hop_prob": 0.40, "anchor_schedule": 3, "anchor_pull": 0.55},
            "theory": ["P8"],
        },
        {
            "id": "conflict_schedule_2",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {"anchor_schedule": 2, "anchor_pull": 0.85},
            "theory": ["P7"],
        },
        {
            "id": "multipath_k3_H",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {},
            "multi_path": True,
            "k": 3,
            "select_by": "tradeoff_harmonic",
            "theory": ["G2"],
        },
        {
            "id": "multipath_k5_H",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {},
            "multi_path": True,
            "k": 5,
            "select_by": "tradeoff_harmonic",
            "theory": ["P5", "G1", "G2", "G3", "B4"],
        },
        {
            "id": "multipath_k5_C",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {},
            "multi_path": True,
            "k": 5,
            "select_by": "creativity_score",
            "theory": ["G1"],
        },
        {
            "id": "multipath_k5_R",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {},
            "multi_path": True,
            "k": 5,
            "select_by": "reasoning_trace_score",
            "theory": ["G1"],
        },
        {
            "id": "multipath_k7_H",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {},
            "multi_path": True,
            "k": 7,
            "select_by": "tradeoff_harmonic",
            "theory": ["G3"],
        },
        {
            "id": "incubation_alt",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {},
            "schedule": "incubation",
            "theory": ["I1"],
        },
        {
            "id": "two_phase",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {},
            "schedule": "two_phase",
            "theory": ["I2"],
        },
        {
            "id": "wm_protect_hotset",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {},
            "wm": "protect",
            "theory": ["P6"],
        },
        {
            "id": "wm_truncate_drop",
            "mode": "creative_burst_v2",
            "use_for_v2": True,
            "knobs": {},
            "wm": "truncate",
            "theory": ["P6"],
        },
    ]


def _typ(v: Any) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _mean(xs: Sequence[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def _make_hopper(spans: Sequence[Any], seed: int, cond: dict[str, Any]) -> CreativeBurstHopper:
    knobs = dict(cond.get("knobs") or {})
    if cond.get("use_for_v2") or cond["mode"] == "creative_burst_v2":
        return CreativeBurstHopper.for_v2(spans, seed=seed, **knobs)
    return CreativeBurstHopper(
        spans, seed=seed, **{k: v for k, v in knobs.items() if k in ("anchor_pull",)}
    )


def _wm_spans(spans: list[Any], mode: str) -> tuple[list[Any], bool]:
    """Simulate protect_compact hot-set vs truncate (drop mid protect)."""
    if mode == "protect":
        # Keep protect + drop noise confounders when unprotected
        hot = filter_spans_for_burst(spans, drop_noise=True)
        return (hot if hot else spans), False
    if mode == "truncate":
        # Drop ~half of mid-document non-edge spans; strip protect flags on mid
        out = []
        n = len(spans)
        for i, s in enumerate(spans):
            # keep head/tail
            if i < max(1, n // 5) or i >= n - max(1, n // 5):
                out.append(s)
                continue
            typ = _typ(s.typology)
            if typ in ("goal", "constraint", "outcome") and getattr(s, "protect", False):
                # goal neglect: drop mid protect anchors
                continue
            if typ in ("noise", "confounder", "lexical"):
                continue
            # clone-like: unset protect conceptually by rebuilding via filter
            out.append(s)
        neglected = any(
            getattr(s, "protect", False) and _typ(s.typology) in ("goal", "constraint")
            for s in spans
        ) and not any(
            getattr(s, "protect", False) and _typ(s.typology) in ("goal", "constraint")
            for s in out
        )
        return (out if len(out) >= 3 else spans[: max(3, n // 2)]), neglected
    return spans, False


def _scheduled_path(
    spans: Sequence[Any],
    *,
    seed: int,
    n_hops: int,
    schedule: str,
    base_knobs: dict[str, Any],
) -> Any:
    """Incubation (alt knobs each hop block) or two-phase diverge→converge."""
    div_knobs = {
        **base_knobs,
        "novelty_weight": 1.55,
        "anchor_pull": 0.25,
        "anchor_schedule": 0,
        "side_hop_prob": 0.32,
        "layer_bias": 0.2,
    }
    conv_knobs = {
        **base_knobs,
        "novelty_weight": 0.7,
        "anchor_pull": 0.95,
        "anchor_schedule": 2,
        "side_hop_prob": 0.05,
        "layer_bias": 0.7,
    }
    half = max(1, n_hops // 2)
    if schedule == "two_phase":
        h1 = CreativeBurstHopper.for_v2(spans, seed=seed, **div_knobs)
        p1 = h1.burst_path(seed=0, n_hops=half, mode="creative_burst_v2")
        # Continue from last span with convergent hopper for remaining hops
        h2 = CreativeBurstHopper.for_v2(spans, seed=seed + 1, **conv_knobs)
        start = p1.span_ids[-1] if p1.span_ids else 0
        p2 = h2.burst_path(seed=start, n_hops=max(0, n_hops - half), mode="creative_burst_v2")
        # Merge unique continuation
        seen = set(p1.span_ids)
        merged_ids = list(p1.span_ids)
        for sid in p2.span_ids:
            if sid not in seen:
                merged_ids.append(sid)
                seen.add(sid)
        from intentisolates.types import BurstPath

        typ_path = [_typ(h2.by_id[i].typology) if i in h2.by_id else "?" for i in merged_ids]
        # prefer first hopper map
        typ_path = []
        by = {**h1.by_id, **h2.by_id}
        for i in merged_ids:
            typ_path.append(_typ(by[i].typology) if i in by else "?")
        return BurstPath(
            seed_id=p1.seed_id,
            hops=list(p1.hops) + list(p2.hops),
            span_ids=merged_ids,
            typology_path=typ_path,
            mode="creative_burst_v2",
            summary="two_phase",
            metadata={"schedule": "two_phase"},
        )
    # incubation: alternate every 2 hops
    from intentisolates.types import BurstPath

    cur_ids: list[str] = []
    hops_all = []
    start_seed: Any = 0
    remaining = n_hops
    block = 0
    while remaining > 0:
        kn = div_knobs if block % 2 == 0 else conv_knobs
        take = min(2, remaining)
        h = CreativeBurstHopper.for_v2(spans, seed=seed + block, **kn)
        p = h.burst_path(seed=start_seed, n_hops=take, mode="creative_burst_v2")
        for sid in p.span_ids:
            if sid not in cur_ids:
                cur_ids.append(sid)
        hops_all.extend(p.hops)
        start_seed = cur_ids[-1] if cur_ids else 0
        remaining -= take
        block += 1
    by = CreativeBurstHopper.for_v2(spans, seed=seed).by_id
    typ_path = [_typ(by[i].typology) if i in by else "?" for i in cur_ids]
    return BurstPath(
        seed_id=str(cur_ids[0] if cur_ids else ""),
        hops=hops_all,
        span_ids=cur_ids,
        typology_path=typ_path,
        mode="creative_burst_v2",
        summary="incubation",
        metadata={"schedule": "incubation"},
    )


def _path_metrics(path: Any, spans: Sequence[Any], hopper: CreativeBurstHopper, meter: CreativityMeter) -> dict[str, Any]:
    report = meter.score_burst(path, spans, motif_neighbors=hopper._motif_neighbors)
    return {
        "typology_entropy": typology_path_entropy(path.typology_path),
        "n_unique_typologies": len(set(path.typology_path)),
        "layer_monotonicity": layer_path_monotonicity(spans, path.span_ids),
        "anchor_R": report.anchor_visit_rate,
        "constraint_fidelity": report.constraint_fidelity,
        "C": report.creativity_score,
        "R": report.reasoning_trace_score,
        "CxR": report.tradeoff_product,
        "H": report.tradeoff_harmonic,
        "novelty": report.novelty,
        "flexibility": report.flexibility,
        "path_len": len(path.span_ids),
        "typology_path": list(path.typology_path),
    }


def _soft_causal(fix_text: str, path: Any, spans: Sequence[Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"ok": False}
    try:
        from intentisolates.causal import LayerCausalSuite

        suite = LayerCausalSuite.from_text(fix_text)
        result = suite.run(outcome_hint="outcome", mock_iv=True)
        out["ok"] = True
        out["n_indication"] = len(result.indications)
        out["n_causation"] = len(result.causation_edges)
        # Overlap: visited typologies vs top indication / causation feature names
        visited_typs = set(path.typology_path)
        ind_hits = 0
        for s in result.indications[:8]:
            name = str(getattr(s, "feature", "") or getattr(s, "column", "") or "").lower()
            if any(t in name for t in visited_typs):
                ind_hits += 1
        cau_hits = 0
        f_vals = []
        for e in result.causation_edges[:8]:
            name = str(getattr(e, "endogenous", "") or getattr(e, "x", "") or "").lower()
            if any(t in name for t in visited_typs):
                cau_hits += 1
            f_vals.append(float(getattr(e, "first_stage_f", 0.0) or 0.0))
        out["indication_overlap"] = ind_hits
        out["causation_overlap"] = cau_hits
        out["mean_first_stage_f"] = _mean(f_vals) if f_vals else 0.0
        # burst Z: count early-layer spans in path
        by = {s.id: s for s in spans}
        early = mid = 0
        for sid in path.span_ids:
            s = by.get(sid)
            if not s:
                continue
            ly = s.layer if isinstance(s.layer, int) else 2
            if isinstance(ly, str) and ly[1:].isdigit():
                ly = int(ly[1:])
            if int(ly) <= 1:
                early += 1
            else:
                mid += 1
        out["burst_early_z_count"] = early
        out["burst_mid_x_count"] = mid
    except Exception as exc:  # noqa: BLE001
        out["error"] = str(exc)
    return out


def run(*, n_hops: int, seed: int, n_seeds: int, out_dir: Path) -> dict[str, Any]:
    meter = CreativityMeter()
    conditions = _conditions()
    rows: list[dict[str, Any]] = []
    causal_rows: list[dict[str, Any]] = []

    for fix in FIXTURES:
        base_spans = identify_span_isolates(fix["text"])
        for cond in conditions:
            trial_metrics: list[dict[str, Any]] = []
            neglect_flags: list[bool] = []
            for offset in range(n_seeds):
                s = seed + offset * 17
                spans = list(base_spans)
                neglected = False
                if cond.get("wm"):
                    spans, neglected = _wm_spans(spans, cond["wm"])
                    neglect_flags.append(neglected)
                if len(spans) < 2:
                    spans = list(base_spans)

                if cond.get("schedule"):
                    path = _scheduled_path(
                        spans, seed=s, n_hops=n_hops, schedule=cond["schedule"], base_knobs=cond.get("knobs") or {}
                    )
                    hopper = CreativeBurstHopper.for_v2(spans, seed=s)
                elif cond.get("multi_path"):
                    path, _ = multi_path_burst(
                        spans,
                        n_hops=n_hops,
                        mode=cond["mode"],
                        k=int(cond.get("k", 5)),
                        seed=s,
                        select_by=str(cond.get("select_by", "tradeoff_harmonic")),
                        hopper_kwargs=cond.get("knobs") or None,
                    )
                    hopper = _make_hopper(spans, s, cond)
                else:
                    hopper = _make_hopper(spans, s, cond)
                    path = hopper.burst_path(seed=offset % max(1, len(hopper.ordered)), n_hops=n_hops, mode=cond["mode"])

                m = _path_metrics(path, spans, hopper, meter)
                m["goal_neglect_under_compact"] = neglected
                trial_metrics.append(m)

                if fix["kind"] == "causal" and cond["id"] in (
                    "creative_burst_v2",
                    "multipath_k5_H",
                    "divergent_guilford",
                    "convergent_constrained",
                    "random",
                ):
                    c = _soft_causal(fix["text"], path, spans)
                    if c.get("ok"):
                        causal_rows.append({"fixture_id": fix["id"], "condition": cond["id"], "seed": s, **c})

            avg_keys = [
                "typology_entropy",
                "n_unique_typologies",
                "layer_monotonicity",
                "anchor_R",
                "constraint_fidelity",
                "C",
                "R",
                "CxR",
                "H",
                "novelty",
                "flexibility",
                "path_len",
            ]
            avg = {k: _mean([float(m[k]) for m in trial_metrics]) for k in avg_keys}
            rows.append(
                {
                    "fixture_id": fix["id"],
                    "fixture_kind": fix["kind"],
                    "condition": cond["id"],
                    "mode": cond["mode"],
                    "n_spans": len(base_spans),
                    "n_seeds": n_seeds,
                    **avg,
                    "goal_neglect_rate": _mean([1.0 if f else 0.0 for f in neglect_flags]) if neglect_flags else 0.0,
                    "example_typology_path": trial_metrics[0]["typology_path"] if trial_metrics else [],
                    "orchestration": orchestration_meta(
                        stage="burst_explore",
                        goal_neglect_under_compact=bool(avg.get("goal_neglect_rate", 0) > 0.5),
                        theory_ids=list(cond.get("theory") or []),
                    ),
                }
            )

    # Aggregate by condition
    by_cond: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(r)

    summary = []
    for cond in conditions:
        rs = by_cond[cond["id"]]
        summary.append(
            {
                "condition": cond["id"],
                "mode": cond["mode"],
                "n": len(rs),
                "avg_C": _mean([r["C"] for r in rs]),
                "avg_R": _mean([r["R"] for r in rs]),
                "avg_H": _mean([r["H"] for r in rs]),
                "avg_CxR": _mean([r["CxR"] for r in rs]),
                "avg_entropy": _mean([r["typology_entropy"] for r in rs]),
                "avg_anchor_R": _mean([r["anchor_R"] for r in rs]),
                "avg_layer_mono": _mean([r["layer_monotonicity"] for r in rs]),
                "avg_constraint_fidelity": _mean([r["constraint_fidelity"] for r in rs]),
                "avg_novelty": _mean([r["novelty"] for r in rs]),
                "avg_flexibility": _mean([r["flexibility"] for r in rs]),
                "avg_goal_neglect": _mean([r["goal_neglect_rate"] for r in rs]),
            }
        )
    sm = {s["condition"]: s for s in summary}

    # Per-fixture sign consistency for claim adjudication
    def _fixture_means(cond_id: str, key: str) -> dict[str, float]:
        out: dict[str, float] = {}
        for r in by_cond.get(cond_id, []):
            out[r["fixture_id"]] = float(r[key])
        return out

    def _compare(
        a: str,
        b: str,
        key: str,
        *,
        op: str = ">",
        eps: float = 0.0,
    ) -> dict[str, Any]:
        fa, fb = _fixture_means(a, key), _fixture_means(b, key)
        common = sorted(set(fa) & set(fb))
        if not common:
            return {"ok": False, "reason": "no fixtures"}
        deltas = [fa[f] - fb[f] for f in common]
        mean_a = _mean([fa[f] for f in common])
        mean_b = _mean([fb[f] for f in common])
        if op == ">":
            wins = sum(1 for d in deltas if d > eps)
            mean_ok = mean_a > mean_b + eps
        elif op == ">=":
            wins = sum(1 for d in deltas if d >= -eps)
            mean_ok = mean_a >= mean_b - eps
        elif op == "<":
            wins = sum(1 for d in deltas if d < -eps)
            mean_ok = mean_a < mean_b - eps
        else:
            wins = 0
            mean_ok = False
        majority = wins >= max(1, (len(common) + 1) // 2)
        if mean_ok and majority:
            verdict = "supported"
            strength = "strong" if wins >= len(common) - 1 and abs(mean_a - mean_b) >= 0.03 else "moderate"
        elif mean_ok or majority:
            verdict = "mixed"
            strength = "weak"
        else:
            verdict = "rejected"
            strength = "moderate" if abs(mean_a - mean_b) >= 0.03 else "weak"
        return {
            "ok": True,
            "mean_a": mean_a,
            "mean_b": mean_b,
            "delta": round(mean_a - mean_b, 4),
            "fixture_wins": wins,
            "n_fixtures": len(common),
            "verdict": verdict,
            "strength": strength,
        }

    claim_evidence: list[dict[str, Any]] = []
    # Explicit claim checks
    checks = [
        ("P1a", "H(v2)>H(random)", lambda: _compare("creative_burst_v2", "random", "H", op=">")),
        ("P1b", "C(v2) within 0.05 of C(random)", None),
        ("P2", "anchor_R(v2)>anchor_R(random)", lambda: _compare("creative_burst_v2", "random", "anchor_R", op=">")),
        ("P3", "mono(layer_cot)>=mono(divergent)", lambda: _compare("layer_cot", "divergent_guilford", "layer_monotonicity", op=">=")),
        ("P4a", "C(div)>C(conv)", lambda: _compare("divergent_guilford", "convergent_constrained", "C", op=">")),
        ("P4b", "entropy(div)>=entropy(conv)", lambda: _compare("divergent_guilford", "convergent_constrained", "typology_entropy", op=">=")),
        ("P5", "H(multipath_H)>=H(v2)", lambda: _compare("multipath_k5_H", "creative_burst_v2", "H", op=">=")),
        ("P6a", "protect_hotset R >= truncate R", lambda: _compare("wm_protect_hotset", "wm_truncate_drop", "R", op=">=")),
        ("P6b", "protect_hotset anchor_R >= truncate", lambda: _compare("wm_protect_hotset", "wm_truncate_drop", "anchor_R", op=">=")),
        ("P7", "conflict_sched H >= v2 H", lambda: _compare("conflict_schedule_2", "creative_burst_v2", "H", op=">=")),
        ("P8a", "sidehop C >= convergent C", lambda: _compare("insight_sidehop", "convergent_constrained", "C", op=">=")),
        ("P8b", "sidehop R not much below convergent (delta>-0.08)", None),
        ("L1a", "motif R > v2 R", lambda: _compare("motif_jump", "creative_burst_v2", "R", op=">")),
        ("L1b", "motif C < v2 C", lambda: _compare("motif_jump", "creative_burst_v2", "C", op="<")),
        ("L2", "v2 R > v1 R", lambda: _compare("creative_burst_v2", "creative_burst_v1", "R", op=">")),
        ("G1", "mp_H R >= mp_C R", lambda: _compare("multipath_k5_H", "multipath_k5_C", "R", op=">=")),
        ("G2", "k5 H >= k3 H", lambda: _compare("multipath_k5_H", "multipath_k3_H", "H", op=">=")),
        ("G3", "k7 H >= k5 H", lambda: _compare("multipath_k7_H", "multipath_k5_H", "H", op=">=")),
        ("PP1", "precision_high R >= precision_low R", lambda: _compare("precision_high", "precision_low", "R", op=">=")),
        ("PP2", "precision_low C >= precision_high C", lambda: _compare("precision_low", "precision_high", "C", op=">=")),
        ("I1", "incubation H >= divergent H", lambda: _compare("incubation_alt", "divergent_guilford", "H", op=">=")),
        ("I2", "two_phase H >= v2 H", lambda: _compare("two_phase", "creative_burst_v2", "H", op=">=")),
        ("PL1", "layer_cot H >= divergent H", lambda: _compare("layer_cot", "divergent_guilford", "H", op=">=")),
        ("S1", "v2 H >= linear H", lambda: _compare("creative_burst_v2", "linear", "H", op=">=")),
        ("S2", "v1 entropy >= linear", lambda: _compare("creative_burst_v1", "linear", "typology_entropy", op=">=")),
        ("S3", "motif mono >= divergent mono", lambda: _compare("motif_jump", "divergent_guilford", "layer_monotonicity", op=">=")),
        ("B4", "mp_H R >= random R", lambda: _compare("multipath_k5_H", "random", "R", op=">=")),
    ]

    for cid, pred, fn in checks:
        if fn is None:
            if cid == "P1b":
                ca, cb = sm.get("creative_burst_v2", {}), sm.get("random", {})
                d = abs(float(ca.get("avg_C", 0)) - float(cb.get("avg_C", 0)))
                ok = d <= 0.05
                claim_evidence.append(
                    {
                        "id": cid,
                        "prediction": pred,
                        "metrics": f"C(v2)={ca.get('avg_C')}, C(rand)={cb.get('avg_C')}, |Δ|={d:.4f}",
                        "verdict": "supported" if ok else "rejected",
                        "strength": "moderate" if ok else "weak",
                        "delta": round(d, 4),
                    }
                )
            elif cid == "P8b":
                ca, cb = sm.get("insight_sidehop", {}), sm.get("convergent_constrained", {})
                d = float(ca.get("avg_R", 0)) - float(cb.get("avg_R", 0))
                ok = d > -0.08
                claim_evidence.append(
                    {
                        "id": cid,
                        "prediction": pred,
                        "metrics": f"R(side)={ca.get('avg_R')}, R(conv)={cb.get('avg_R')}, Δ={d:.4f}",
                        "verdict": "supported" if ok else "rejected",
                        "strength": "moderate" if ok else "weak",
                        "delta": round(d, 4),
                    }
                )
            continue
        res = fn()
        if not res.get("ok"):
            claim_evidence.append(
                {
                    "id": cid,
                    "prediction": pred,
                    "metrics": res.get("reason", "n/a"),
                    "verdict": "untested",
                    "strength": "weak",
                }
            )
            continue
        claim_evidence.append(
            {
                "id": cid,
                "prediction": pred,
                "metrics": (
                    f"mean_a={res['mean_a']:.4f} mean_b={res['mean_b']:.4f} "
                    f"Δ={res['delta']:.4f} wins={res['fixture_wins']}/{res['n_fixtures']}"
                ),
                "verdict": res["verdict"],
                "strength": res["strength"],
                "delta": res["delta"],
                "fixture_wins": res["fixture_wins"],
                "n_fixtures": res["n_fixtures"],
            }
        )

    # Causal B1/B2 soft
    if causal_rows:
        by_c: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in causal_rows:
            by_c[r["condition"]].append(r)
        burst = by_c.get("creative_burst_v2") or by_c.get("multipath_k5_H") or []
        rnd = by_c.get("random") or []
        if burst and rnd:
            bf = _mean([r["mean_first_stage_f"] for r in burst])
            rf = _mean([r["mean_first_stage_f"] for r in rnd])
            claim_evidence.append(
                {
                    "id": "B1",
                    "prediction": "burst path mean first_stage_F >= random (mock IV)",
                    "metrics": f"F(burst)={bf:.4f} F(random)={rf:.4f}",
                    "verdict": "supported" if bf >= rf else "rejected",
                    "strength": "weak",
                    "note": "mock_iv / synthetic rows — exploratory only",
                }
            )
        conv = by_c.get("convergent_constrained") or []
        div = by_c.get("divergent_guilford") or []
        if conv and div:
            cc = _mean([r["causation_overlap"] for r in conv])
            dc = _mean([r["causation_overlap"] for r in div])
            claim_evidence.append(
                {
                    "id": "B2",
                    "prediction": "high-R (convergent) causation_overlap >= divergent",
                    "metrics": f"cau_ov(conv)={cc:.4f} cau_ov(div)={dc:.4f}",
                    "verdict": "supported" if cc >= dc else "rejected",
                    "strength": "weak",
                    "note": "soft name overlap proxy",
                }
            )
    else:
        claim_evidence.append(
            {
                "id": "B1",
                "prediction": "burst Z first-stage F >= random",
                "metrics": "causal suite unavailable or no causal fixture rows",
                "verdict": "untested",
                "strength": "weak",
            }
        )
        claim_evidence.append(
            {
                "id": "B2",
                "prediction": "high-R causation alignment",
                "metrics": "no causal rows",
                "verdict": "untested",
                "strength": "weak",
            }
        )

    # Counts
    counts = {"supported": 0, "rejected": 0, "mixed": 0, "untested": 0}
    for c in claim_evidence:
        counts[c["verdict"]] = counts.get(c["verdict"], 0) + 1

    ranked = sorted(summary, key=lambda s: (-s["avg_H"], -s["avg_R"], -s["avg_C"]))
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "backend": "intentisolates",
        "n_hops": n_hops,
        "seed": seed,
        "n_seeds": n_seeds,
        "n_fixtures": len(FIXTURES),
        "conditions": [c["id"] for c in conditions],
        "claims_enumerated": [c["id"] for c in CLAIMS],
        "summary_table": summary,
        "ranked_by_H": [s["condition"] for s in ranked],
        "claim_evidence": claim_evidence,
        "evidence_counts": counts,
        "rows": rows,
        "causal_rows": causal_rows,
        "verdict": [
            f"Claims: supported={counts['supported']} rejected={counts['rejected']} "
            f"mixed={counts['mixed']} untested={counts['untested']}",
            "Best H: " + ", ".join(f"{s['condition']}={s['avg_H']:.3f}" for s in ranked[:5]),
        ],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"theory_corpus_sweep_{stamp}.json"
    md_path = out_dir / f"theory_corpus_sweep_{stamp}.md"
    latest_json = out_dir / "theory_corpus_sweep_latest.json"
    latest_md = out_dir / "theory_corpus_sweep_latest.md"
    evidence_md = out_dir / "CLAIM_EVIDENCE_TABLE.md"
    text = json.dumps(payload, indent=2)
    json_path.write_text(text, encoding="utf-8")
    latest_json.write_text(text, encoding="utf-8")
    md = _render_md(payload)
    md_path.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")
    evidence_md.write_text(_render_evidence(payload), encoding="utf-8")
    payload["paths"] = {
        "json": str(json_path),
        "markdown": str(md_path),
        "latest_json": str(latest_json),
        "latest_md": str(latest_md),
        "claim_evidence": str(evidence_md),
    }
    return payload


def _render_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Theory corpus sweep",
        "",
        f"- Created: `{payload['created_at']}`",
        f"- Hops: `{payload['n_hops']}` · fixtures: `{payload['n_fixtures']}` · seeds: `{payload['n_seeds']}`",
        f"- Evidence: `{payload['evidence_counts']}`",
        "",
        "## Summary (CreativityMeter)",
        "",
        "| condition | C | R | H | entropy | anchor_R | layer_mono |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in payload["summary_table"]:
        lines.append(
            f"| {s['condition']} | {s['avg_C']:.3f} | {s['avg_R']:.3f} | {s['avg_H']:.3f} | "
            f"{s['avg_entropy']:.3f} | {s['avg_anchor_R']:.3f} | {s['avg_layer_mono']:.3f} |"
        )
    lines += ["", "## Ranked by H", ""]
    for i, name in enumerate(payload["ranked_by_H"], 1):
        lines.append(f"{i}. `{name}`")
    lines += ["", "## Verdict", ""]
    for v in payload["verdict"]:
        lines.append(f"- {v}")
    lines.append("")
    return "\n".join(lines)


def _render_evidence(payload: dict[str, Any]) -> str:
    lines = [
        "# Claim evidence table (theory_corpus_sweep)",
        "",
        f"- Created: `{payload['created_at']}`",
        f"- Counts: **{payload['evidence_counts']}**",
        "",
        "| ID | Prediction | Metrics | Verdict | Strength |",
        "| --- | --- | --- | --- | --- |",
    ]
    for c in payload["claim_evidence"]:
        lines.append(
            f"| {c['id']} | {c['prediction']} | {c.get('metrics', '')} | "
            f"**{c['verdict']}** | {c.get('strength', '')} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hops", type=int, default=5)
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--out-dir", type=Path, default=_ROOT / "experiments" / "results")
    args = p.parse_args(list(argv) if argv is not None else None)
    payload = run(n_hops=args.hops, seed=args.seed, n_seeds=args.seeds, out_dir=args.out_dir)
    print("\n=== Theory corpus sweep (C / R / H) ===")
    for s in payload["summary_table"]:
        print(
            f"{s['condition']:24s}  C={s['avg_C']:.3f}  R={s['avg_R']:.3f}  "
            f"H={s['avg_H']:.3f}  ent={s['avg_entropy']:.3f}  "
            f"anchor_R={s['avg_anchor_R']:.3f}"
        )
    print("\nEvidence counts:", payload["evidence_counts"])
    for v in payload["verdict"]:
        print(" ", v)
    print(f"\nWrote {payload['paths']['markdown']}")
    print(f"Wrote {payload['paths']['claim_evidence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
