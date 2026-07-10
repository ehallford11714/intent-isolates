#!/usr/bin/env python3
"""Iterative reasoning-trace "training" — RT-guided policy hill-climb (≥10 epochs).

Each epoch evaluates a hop/multipath/protect policy on a fixed fixture×seed set,
logs a reasoning-trace summary, then updates knobs using NEXT_EXPERIMENTS_REASONING_TRACE
priorities (RT1–RT5 / RT3 hybrid):

  Epochs 0–1: baseline floor (v2 single-path, then multipath_H)
  Epochs 2–3: RT1 multipath value-fn (select_by ∈ {H,R,C,iv_diag}, k∈{3,5,7})
  Epochs 4–5: RT2 protect_compact→burst coupling (protect on/off)
  Epochs 6–7: RT4/RT5 conflict schedule + layer_bias / soft mono nudge
  Epochs 8–9: RT3 IV-diag deepen OR hybrid of best RT1+RT2 knobs

Update rule (transparent, not neural):
  Primary objective = mean H; soft floor on mean R (default 0.78).
  Coordinate / evolutionary steps cite ``guided_by`` RT id + ``action`` text.

Usage::

    python experiments/iterative_reasoning_training.py
    python experiments/iterative_reasoning_training.py --epochs 10 --fixtures 4 --seeds 3
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from intentisolates import CreativityMeter, CreativeBurstHopper, identify_span_isolates  # noqa: E402
from intentisolates.span_burst import filter_spans_for_burst  # noqa: E402

sys.path.insert(0, str(_ROOT / "experiments"))
from theory_corpus_sweep import FIXTURES  # type: ignore  # noqa: E402

# ---------------------------------------------------------------------------
# Epoch → RT guidance map (documented in report)
# ---------------------------------------------------------------------------
EPOCH_RT_MAP: dict[int, dict[str, str]] = {
    0: {"guided_by": "baseline", "phase": "floor_v2_single", "note": "Default creative_burst_v2 knobs, no multipath"},
    1: {"guided_by": "baseline", "phase": "floor_multipath_H", "note": "Enable multipath k=5 select_by=H (P5/G2 floor)"},
    2: {"guided_by": "RT1", "phase": "value_fn_bakeoff", "note": "Mutate select_by / k; elite by H with R floor"},
    3: {
        "guided_by": "RT1",
        "phase": "value_fn_refine",
        "note": "Keep elite selection rule; small k/select refinement",
    },
    4: {"guided_by": "RT2", "phase": "protect_on", "note": "Turn protect_compact filter on; mid_constraint + H"},
    5: {
        "guided_by": "RT2",
        "phase": "protect_toggle",
        "note": "Compare protect on vs off; keep better on H/R/mid",
    },
    6: {
        "guided_by": "RT4",
        "phase": "conflict_schedule",
        "note": "Grid anchor_schedule / anchor_pull (P7 conflict)",
    },
    7: {
        "guided_by": "RT5",
        "phase": "layer_mono",
        "note": "Raise layer_bias toward mono without motif C-collapse",
    },
    8: {
        "guided_by": "RT3",
        "phase": "iv_diag_or_hybrid",
        "note": "Prefer iv_diag select or hybrid RT1+RT2 elite knobs",
    },
    9: {
        "guided_by": "RT3",
        "phase": "hybrid_polish",
        "note": "Final hill-climb on novelty/anchor/layer around elite",
    },
}

SELECT_KEYS = {
    "H": "tradeoff_harmonic",
    "R": "reasoning_trace_score",
    "C": "creativity_score",
    "iv_diag": "iv_diag",
}

R_FLOOR_DEFAULT = 0.78


@dataclass
class Policy:
    """Hop + multipath + protect policy knobs."""

    novelty_weight: float = 1.10
    anchor_pull: float = 0.70
    layer_bias: float = 0.55
    motif_weight: float = 0.45
    anchor_schedule: int = 3
    side_hop_prob: float = 0.18
    multipath: bool = False
    k: int = 5
    select_by: str = "H"  # H | R | C | iv_diag
    protect_compact: bool = False
    soft_mono_gate: bool = False  # RT5: prefer forward layer hops when scoring
    # RT4b: mid-path adaptive schedule (None | loosen_on_calm | tighten_on_thrash)
    adaptive_policy: str | None = None
    thrash_threshold: float = 0.55

    def knobs(self) -> dict[str, Any]:
        return {
            "novelty_weight": self.novelty_weight,
            "anchor_pull": self.anchor_pull,
            "layer_bias": self.layer_bias,
            "motif_weight": self.motif_weight,
            "anchor_schedule": int(self.anchor_schedule),
            "side_hop_prob": self.side_hop_prob,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.knobs(),
            "multipath": self.multipath,
            "k": int(self.k),
            "select_by": self.select_by,
            "protect_compact": self.protect_compact,
            "soft_mono_gate": self.soft_mono_gate,
            "adaptive_policy": self.adaptive_policy,
            "thrash_threshold": float(self.thrash_threshold),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Policy":
        return cls(
            novelty_weight=float(d.get("novelty_weight", 1.10)),
            anchor_pull=float(d.get("anchor_pull", 0.70)),
            layer_bias=float(d.get("layer_bias", 0.55)),
            motif_weight=float(d.get("motif_weight", 0.45)),
            anchor_schedule=int(d.get("anchor_schedule", 3)),
            side_hop_prob=float(d.get("side_hop_prob", 0.18)),
            multipath=bool(d.get("multipath", False)),
            k=int(d.get("k", 5)),
            select_by=str(d.get("select_by", "H")),
            protect_compact=bool(d.get("protect_compact", False)),
            soft_mono_gate=bool(d.get("soft_mono_gate", False)),
            adaptive_policy=d.get("adaptive_policy"),
            thrash_threshold=float(d.get("thrash_threshold", 0.55)),
        )


def _mean(xs: Sequence[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def _typ(v: Any) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _layer_int(layer: Any) -> int:
    if layer is None:
        return 2
    if isinstance(layer, int):
        return layer
    s = str(layer)
    if s.isdigit():
        return int(s)
    if s.upper().startswith("L") and s[1:].isdigit():
        return int(s[1:])
    return 2


def _early_layer_frac(path_ids: Sequence[str], spans: Sequence[Any]) -> float:
    by_id = {s.id: s for s in spans}
    layers = [_layer_int(by_id[i].layer) for i in path_ids if i in by_id]
    if not layers:
        return 0.0
    return sum(1 for L in layers if L <= 1) / len(layers)


def _iv_diag(report: Any, path_ids: Sequence[str], spans: Sequence[Any]) -> float:
    return (
        0.5 * float(report.anchor_visit_rate)
        + 0.3 * float(report.layer_monotonicity)
        + 0.2 * _early_layer_frac(path_ids, spans)
    )


def _apply_protect(spans: list[Any], protect: bool) -> tuple[list[Any], float]:
    mid_ids = set()
    n = len(spans)
    lo, hi = max(1, n // 5), n - max(1, n // 5)
    for i, s in enumerate(spans):
        if lo <= i < hi and (getattr(s, "protect", False) or _typ(s.typology) in ("goal", "constraint")):
            mid_ids.add(s.id)
    if not protect:
        return list(spans), 1.0 if not mid_ids else 1.0
    pool = filter_spans_for_burst(spans, drop_noise=True)
    if len(pool) < 3:
        pool = list(spans)
    kept = {s.id for s in pool} & mid_ids
    mid_r = (len(kept) / len(mid_ids)) if mid_ids else 1.0
    return pool, mid_r


def _score_select(report: Any, path_ids: Sequence[str], spans: Sequence[Any], select_by: str) -> float:
    if select_by == "iv_diag":
        return _iv_diag(report, path_ids, spans)
    key = SELECT_KEYS.get(select_by, select_by)
    mapping = {
        "tradeoff_harmonic": report.tradeoff_harmonic,
        "creativity_score": report.creativity_score,
        "reasoning_trace_score": report.reasoning_trace_score,
        "anchor_visit_rate": report.anchor_visit_rate,
    }
    return float(mapping[key])


def _thrash_score(typology_path: Sequence[str]) -> float:
    if len(typology_path) < 2:
        return 0.0
    flips = sum(1 for a, b in zip(typology_path, typology_path[1:]) if a != b)
    return flips / (len(typology_path) - 1)


def _adaptive_path(
    pool: list[Any],
    *,
    seed: int,
    n_hops: int,
    knobs: dict[str, Any],
    policy_name: str,
    thrash_threshold: float,
    seed_index: int = 0,
) -> Any:
    """Continuous burst with mid-path schedule adaptation (RT4b)."""
    import random as _random

    from intentisolates.types import BurstHop, BurstPath

    pull_hi = float(knobs.get("anchor_pull", 0.80))
    pull_lo = min(pull_hi, 0.70)
    if policy_name == "loosen_on_calm":
        init_sched, init_pull = 2, pull_hi
    else:
        init_sched, init_pull = 3, pull_lo

    hopper = CreativeBurstHopper.for_v2(
        pool,
        seed=seed,
        **{**knobs, "anchor_schedule": init_sched, "anchor_pull": init_pull},
    )
    hopper._v2_anchor_explicit = True
    start = hopper.ordered[seed_index % max(1, len(hopper.ordered))]
    rng = _random.Random(seed + hash(start.id) % 10_000)
    visited: list[str] = [start.id]
    hops: list[Any] = []
    current = start
    triggered = False
    anchors = {s.id for s in pool if getattr(s, "protect", False)}

    for step in range(max(0, n_hops)):
        if not triggered and len(visited) >= 3:
            typs = [_typ(hopper.by_id[i].typology) for i in visited if i in hopper.by_id]
            thrash = _thrash_score(typs)
            visited_anchors = sum(1 for a in anchors if a in set(visited))
            if policy_name == "loosen_on_calm":
                if thrash < thrash_threshold and visited_anchors >= 1:
                    hopper.anchor_schedule = 3
                    hopper.anchor_pull = pull_lo
                    triggered = True
            else:
                low_anchor = visited_anchors == 0
                if thrash >= thrash_threshold or (low_anchor and thrash >= 0.5):
                    hopper.anchor_schedule = 2
                    hopper.anchor_pull = pull_hi
                    triggered = True
        nxt, score, reason = hopper._next_hop(
            current, visited, mode="creative_burst_v2", rng=rng
        )
        if nxt is None:
            break
        hops.append(
            BurstHop(
                from_id=current.id,
                to_id=nxt.id,
                mode="creative_burst_v2",
                score=round(score, 4),
                reason=reason + (";adapt" if triggered else ""),
            )
        )
        visited.append(nxt.id)
        current = nxt

    typ_path = [_typ(hopper.by_id[i].typology) for i in visited if i in hopper.by_id]
    return BurstPath(
        seed_id=start.id,
        hops=hops,
        span_ids=visited,
        typology_path=typ_path,
        mode="creative_burst_v2",
        summary=f"adaptive_{policy_name}",
        metadata={"triggered": triggered, "policy": policy_name},
    )


def _run_one(
    spans: list[Any],
    policy: Policy,
    *,
    n_hops: int,
    seed: int,
    meter: CreativityMeter,
) -> dict[str, Any]:
    pool, mid_r = _apply_protect(spans, policy.protect_compact)
    knobs = policy.knobs()
    if policy.soft_mono_gate:
        knobs = {**knobs, "layer_bias": min(1.2, knobs["layer_bias"] + 0.15)}

    traces: list[dict[str, Any]] = []
    use_adapt = bool(policy.adaptive_policy)

    if policy.multipath:
        k = max(1, min(policy.k, len(pool)))
        candidates: list[dict[str, Any]] = []
        base = CreativeBurstHopper.for_v2(pool, seed=seed, **knobs)
        for i in range(k):
            if use_adapt:
                path = _adaptive_path(
                    pool,
                    seed=seed + i * 31,
                    n_hops=n_hops,
                    knobs=knobs,
                    policy_name=str(policy.adaptive_policy),
                    thrash_threshold=policy.thrash_threshold,
                    seed_index=i,
                )
                h = CreativeBurstHopper.for_v2(
                    pool, motifs=base.motifs, seed=seed + i * 31, **knobs
                )
            else:
                h = CreativeBurstHopper.for_v2(
                    pool, motifs=base.motifs, seed=seed + i * 31, **knobs
                )
                path = h.burst_path(
                    seed=i % max(1, len(h.ordered)), n_hops=n_hops, mode="creative_burst_v2"
                )
            report = meter.score_burst(path, pool, motif_neighbors=h._motif_neighbors)
            sel = _score_select(report, path.span_ids, pool, policy.select_by)
            candidates.append(
                {
                    "span_ids": list(path.span_ids),
                    "typology_path": list(path.typology_path),
                    "C": report.creativity_score,
                    "R": report.reasoning_trace_score,
                    "H": report.tradeoff_harmonic,
                    "anchor_R": report.anchor_visit_rate,
                    "layer_mono": report.layer_monotonicity,
                    "select_score": sel,
                    "seed_index": i,
                }
            )
        candidates.sort(key=lambda c: (-float(c["select_score"]), c["seed_index"]))
        best = candidates[0]
        traces = [
            {"seed_index": c["seed_index"], "H": c["H"], "R": c["R"], "C": c["C"], "select_score": c["select_score"]}
            for c in candidates
        ]
        return {
            "C": round(best["C"], 4),
            "R": round(best["R"], 4),
            "H": round(best["H"], 4),
            "anchor_R": round(best["anchor_R"], 4),
            "layer_mono": round(best["layer_mono"], 4),
            "mid_constraint_R": round(mid_r, 4),
            "path_span_ids": best["span_ids"],
            "typology_path": best["typology_path"],
            "candidates": traces,
            "pool_n": len(pool),
        }

    if use_adapt:
        path = _adaptive_path(
            pool,
            seed=seed,
            n_hops=n_hops,
            knobs=knobs,
            policy_name=str(policy.adaptive_policy),
            thrash_threshold=policy.thrash_threshold,
            seed_index=0,
        )
        h = CreativeBurstHopper.for_v2(pool, seed=seed, **knobs)
    else:
        h = CreativeBurstHopper.for_v2(pool, seed=seed, **knobs)
        path = h.burst_path(seed=0, n_hops=n_hops, mode="creative_burst_v2")
    report = meter.score_burst(path, pool, motif_neighbors=h._motif_neighbors)
    return {
        "C": round(report.creativity_score, 4),
        "R": round(report.reasoning_trace_score, 4),
        "H": round(report.tradeoff_harmonic, 4),
        "anchor_R": round(report.anchor_visit_rate, 4),
        "layer_mono": round(report.layer_monotonicity, 4),
        "mid_constraint_R": round(mid_r, 4),
        "path_span_ids": list(path.span_ids),
        "typology_path": list(path.typology_path),
        "candidates": [],
        "pool_n": len(pool),
    }


def evaluate_policy(
    policy: Policy,
    fixtures: Sequence[dict[str, Any]],
    *,
    n_hops: int,
    seed: int,
    n_seeds: int,
) -> dict[str, Any]:
    meter = CreativityMeter()
    rows: list[dict[str, Any]] = []
    for fx in fixtures:
        spans = identify_span_isolates(fx["text"], backend="rule")
        if len(spans) < 3:
            continue
        for si in range(n_seeds):
            m = _run_one(spans, policy, n_hops=n_hops, seed=seed + si * 17, meter=meter)
            rows.append({"fixture": fx["id"], "seed_offset": si, **m})
    summary = {
        "avg_C": _mean([r["C"] for r in rows]),
        "avg_R": _mean([r["R"] for r in rows]),
        "avg_H": _mean([r["H"] for r in rows]),
        "avg_anchor_R": _mean([r["anchor_R"] for r in rows]),
        "avg_layer_mono": _mean([r["layer_mono"] for r in rows]),
        "avg_mid_constraint_R": _mean([r["mid_constraint_R"] for r in rows]),
        "n": len(rows),
    }
    return {"summary": summary, "rows": rows}


def _objective(summary: dict[str, float], r_floor: float) -> float:
    """Primary H; penalize R below floor."""
    h = summary["avg_H"]
    r = summary["avg_R"]
    penalty = 0.0 if r >= r_floor else 2.0 * (r_floor - r)
    return h - penalty


def _clamp_policy(p: Policy) -> Policy:
    p.novelty_weight = float(min(1.8, max(0.4, p.novelty_weight)))
    p.anchor_pull = float(min(1.3, max(0.15, p.anchor_pull)))
    p.layer_bias = float(min(1.15, max(0.1, p.layer_bias)))
    p.motif_weight = float(min(0.9, max(0.1, p.motif_weight)))
    p.anchor_schedule = int(min(5, max(0, p.anchor_schedule)))
    p.side_hop_prob = float(min(0.35, max(0.05, p.side_hop_prob)))
    p.k = int(min(7, max(1, p.k)))
    if p.select_by not in SELECT_KEYS:
        p.select_by = "H"
    return p


def update_policy(
    epoch: int,
    current: Policy,
    metrics: dict[str, float],
    history: list[dict[str, Any]],
    *,
    r_floor: float,
    eval_fn,
) -> tuple[Policy, dict[str, Any]]:
    """RT-guided transparent update → (next_policy, update_log)."""
    guide = EPOCH_RT_MAP.get(epoch, {"guided_by": "heuristic", "phase": "generic", "note": ""})
    guided_by = guide["guided_by"]
    phase = guide["phase"]
    nxt = copy.deepcopy(current)
    action = ""
    candidates_tried: list[dict[str, Any]] = []

    def try_policies(variants: list[tuple[str, Policy]]) -> tuple[Policy, str, list[dict[str, Any]]]:
        tried: list[dict[str, Any]] = []
        best_p = current
        best_obj = _objective(metrics, r_floor)
        best_label = "keep"
        for label, pol in variants:
            pol = _clamp_policy(pol)
            res = eval_fn(pol)
            sm = res["summary"]
            obj = _objective(sm, r_floor)
            tried.append({"label": label, "policy": pol.to_dict(), "summary": sm, "objective": round(obj, 4)})
            if obj > best_obj + 1e-6:
                best_obj = obj
                best_p = pol
                best_label = label
        return best_p, best_label, tried

    if epoch == 0:
        # epoch 0 evaluates baseline; schedule multipath for epoch 1
        nxt.multipath = True
        nxt.k = 5
        nxt.select_by = "H"
        action = "Schedule multipath_H (k=5) for epoch 1 floor (baseline→P5)"
        return _clamp_policy(nxt), {
            "guided_by": guided_by,
            "phase": phase,
            "action": action,
            "note": guide["note"],
            "candidates_tried": [],
            "accepted": "schedule_multipath",
        }

    if epoch == 1:
        # already on multipath from epoch0 update; mild novelty nudge toward higher H if flat
        variants = [
            ("keep", copy.deepcopy(current)),
            ("k3_H", Policy(**{**current.to_dict(), "k": 3, "select_by": "H", "multipath": True})),
            ("k5_H", Policy(**{**current.to_dict(), "k": 5, "select_by": "H", "multipath": True})),
            ("k7_H", Policy(**{**current.to_dict(), "k": 7, "select_by": "H", "multipath": True})),
        ]
        best, label, tried = try_policies(variants)
        action = f"Baseline multipath floor: accept {label}"
        return best, {
            "guided_by": guided_by,
            "phase": phase,
            "action": action,
            "note": guide["note"],
            "candidates_tried": tried,
            "accepted": label,
        }

    if epoch in (2, 3):
        # RT1: select_by × k bakeoff / refine (bounded for offline runtime)
        variants: list[tuple[str, Policy]] = [("keep", copy.deepcopy(current))]
        if epoch == 2:
            for sb in ("H", "R", "C", "iv_diag"):
                for k in (3, 5):
                    label = f"mp_k{k}_{sb}"
                    variants.append(
                        (
                            label,
                            Policy(
                                **{
                                    **current.to_dict(),
                                    "multipath": True,
                                    "k": k,
                                    "select_by": sb,
                                }
                            ),
                        )
                    )
            # one k=7 H probe (sweep anchor)
            variants.append(
                (
                    "mp_k7_H",
                    Policy(**{**current.to_dict(), "multipath": True, "k": 7, "select_by": "H"}),
                )
            )
        else:
            # epoch 3: refine around elite
            elite_sb = current.select_by
            for sb in {elite_sb, "H", "iv_diag", "R"}:
                for k in {current.k, 5, 3}:
                    variants.append(
                        (
                            f"mp_k{k}_{sb}",
                            Policy(**{**current.to_dict(), "multipath": True, "k": k, "select_by": sb}),
                        )
                    )
        # dedupe
        seen: set[str] = set()
        uniq: list[tuple[str, Policy]] = []
        for lab, pol in variants:
            key = json.dumps(pol.to_dict(), sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            uniq.append((lab, pol))
        best, label, tried = try_policies(uniq)
        # Insight mapping: if R low → bias toward R/iv_diag; if C low avoid select C
        insight = ""
        if metrics["avg_R"] < r_floor:
            insight = " R below floor → prefer select_by R/iv_diag or H with higher anchor later"
        if metrics.get("avg_C", 1) < 0.65:
            insight += " C low → avoid select_by=C"
        action = f"RT1 value-fn: accept {label}.{insight}"
        return best, {
            "guided_by": guided_by,
            "phase": phase,
            "action": action,
            "note": guide["note"],
            "candidates_tried": tried,
            "accepted": label,
        }

    if epoch in (4, 5):
        # RT2: protect on/off
        variants = [
            ("protect_off", Policy(**{**current.to_dict(), "protect_compact": False})),
            ("protect_on", Policy(**{**current.to_dict(), "protect_compact": True})),
        ]
        if epoch == 5:
            # also try protect + slightly higher anchor
            variants.append(
                (
                    "protect_on_anchor+",
                    Policy(
                        **{
                            **current.to_dict(),
                            "protect_compact": True,
                            "anchor_pull": current.anchor_pull + 0.1,
                            "anchor_schedule": max(2, current.anchor_schedule - 1)
                            if current.anchor_schedule
                            else 2,
                        }
                    ),
                )
            )
        best, label, tried = try_policies(variants)
        # Prefer protect if mid_R and H not hurt
        action = f"RT2 protect coupling: accept {label}"
        return best, {
            "guided_by": guided_by,
            "phase": phase,
            "action": action,
            "note": guide["note"],
            "candidates_tried": tried,
            "accepted": label,
        }

    if epoch == 6:
        # RT4 / RT4b: conflict schedule grid + adaptive_loosen neighborhood
        variants = [("keep", copy.deepcopy(current))]
        for sched in (2, 3, 4):
            for pull in (0.70, 0.85, 1.0):
                variants.append(
                    (
                        f"sched{sched}_pull{pull}",
                        Policy(
                            **{
                                **current.to_dict(),
                                "anchor_schedule": sched,
                                "anchor_pull": pull,
                                "adaptive_policy": None,
                            }
                        ),
                    )
                )
        # RT4b: bake adaptive_loosen into trainer neighborhood
        for thr in (0.40, 0.55, 0.70):
            variants.append(
                (
                    f"adaptive_loosen_{thr}",
                    Policy(
                        **{
                            **current.to_dict(),
                            "anchor_schedule": 2,
                            "anchor_pull": max(0.80, current.anchor_pull),
                            "adaptive_policy": "loosen_on_calm",
                            "thrash_threshold": thr,
                            "multipath": True,
                            "protect_compact": True,
                        }
                    ),
                )
            )
        variants.append(
            (
                "adaptive_tighten_0.55",
                Policy(
                    **{
                        **current.to_dict(),
                        "adaptive_policy": "tighten_on_thrash",
                        "thrash_threshold": 0.55,
                        "multipath": True,
                    }
                ),
            )
        )
        best, label, tried = try_policies(variants)
        action = f"RT4/RT4b conflict schedule + adaptive_loosen: accept {label}"
        return best, {
            "guided_by": guided_by,
            "phase": phase,
            "action": action,
            "note": guide["note"],
            "candidates_tried": tried,
            "accepted": label,
        }

    if epoch == 7:
        # RT5: layer_bias / soft mono
        variants = [
            ("keep", copy.deepcopy(current)),
            ("layer_0.75", Policy(**{**current.to_dict(), "layer_bias": 0.75, "soft_mono_gate": False})),
            ("layer_0.95", Policy(**{**current.to_dict(), "layer_bias": 0.95, "soft_mono_gate": False})),
            ("soft_mono", Policy(**{**current.to_dict(), "layer_bias": 0.70, "soft_mono_gate": True})),
            (
                "layer_cot_like",
                Policy(**{**current.to_dict(), "layer_bias": 0.95, "novelty_weight": 0.9, "side_hop_prob": 0.08}),
            ),
        ]
        best, label, tried = try_policies(variants)
        action = f"RT5 layer_mono intervention: accept {label}"
        return best, {
            "guided_by": guided_by,
            "phase": phase,
            "action": action,
            "note": guide["note"],
            "candidates_tried": tried,
            "accepted": label,
        }

    if epoch in (8, 9):
        # RT3 / hybrid: iv_diag select + polish novelty/anchor/layer around elite
        base = current.to_dict()
        variants = [("keep", copy.deepcopy(current))]
        if epoch == 8:
            variants.extend(
                [
                    (
                        "iv_diag_k5",
                        Policy(**{**base, "multipath": True, "select_by": "iv_diag", "k": 5}),
                    ),
                    (
                        "iv_diag_k7",
                        Policy(**{**base, "multipath": True, "select_by": "iv_diag", "k": 7}),
                    ),
                    (
                        "hybrid_H_protect",
                        Policy(
                            **{
                                **base,
                                "multipath": True,
                                "select_by": "H",
                                "protect_compact": True,
                                "k": max(5, current.k),
                            }
                        ),
                    ),
                ]
            )
        # coordinate ascent on continuous knobs
        deltas = [
            ("novelty+", {"novelty_weight": current.novelty_weight + 0.1}),
            ("novelty-", {"novelty_weight": current.novelty_weight - 0.1}),
            ("anchor+", {"anchor_pull": current.anchor_pull + 0.08}),
            ("anchor-", {"anchor_pull": current.anchor_pull - 0.08}),
            ("layer+", {"layer_bias": current.layer_bias + 0.08}),
            ("layer-", {"layer_bias": current.layer_bias - 0.08}),
        ]
        # insight from metrics
        if metrics["avg_R"] < r_floor:
            deltas = [d for d in deltas if d[0] in ("anchor+", "layer+", "novelty-")] + deltas
        if metrics["avg_C"] < 0.68:
            deltas = [d for d in deltas if d[0] in ("novelty+", "anchor-")] + deltas
        if metrics["avg_layer_mono"] < 0.65:
            deltas = [d for d in deltas if d[0].startswith("layer")] + deltas

        for lab, over in deltas:
            variants.append((lab, Policy(**{**base, **over})))

        # dedupe
        seen = set()
        uniq = []
        for lab, pol in variants:
            key = json.dumps(pol.to_dict(), sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            uniq.append((lab, pol))
        best, label, tried = try_policies(uniq)
        action = f"RT3/hybrid polish: accept {label}"
        return best, {
            "guided_by": guided_by,
            "phase": phase,
            "action": action,
            "note": guide["note"],
            "candidates_tried": tried,
            "accepted": label,
        }

    # fallback coordinate climb
    variants = [
        ("keep", copy.deepcopy(current)),
        ("novelty+", Policy(**{**current.to_dict(), "novelty_weight": current.novelty_weight + 0.1})),
        ("anchor+", Policy(**{**current.to_dict(), "anchor_pull": current.anchor_pull + 0.1})),
    ]
    best, label, tried = try_policies(variants)
    return best, {
        "guided_by": guided_by,
        "phase": phase,
        "action": f"Generic climb: {label}",
        "note": guide.get("note", ""),
        "candidates_tried": tried,
        "accepted": label,
    }


def run_training(
    *,
    n_epochs: int = 10,
    n_hops: int = 5,
    seed: int = 17,
    n_seeds: int = 3,
    n_fixtures: int = 4,
    r_floor: float = R_FLOOR_DEFAULT,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    out_dir = out_dir or (_ROOT / "experiments" / "results" / "iterative_epochs")
    out_dir.mkdir(parents=True, exist_ok=True)
    fixtures = FIXTURES[:n_fixtures]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    policy = Policy()  # v2 defaults
    history: list[dict[str, Any]] = []
    epoch_summaries: list[dict[str, Any]] = []

    # Cache evals within an epoch update to avoid duplicate work for identical policies
    eval_cache: dict[str, dict[str, Any]] = {}

    def eval_fn(pol: Policy) -> dict[str, Any]:
        key = json.dumps(pol.to_dict(), sort_keys=True)
        if key not in eval_cache:
            eval_cache[key] = evaluate_policy(
                pol, fixtures, n_hops=n_hops, seed=seed, n_seeds=n_seeds
            )
        return eval_cache[key]

    for t in range(n_epochs):
        eval_cache.clear()  # refresh each epoch (same fixtures; policies differ)
        guide = EPOCH_RT_MAP.get(t, {"guided_by": "heuristic", "phase": "generic", "note": ""})
        result = eval_fn(policy)
        summary = result["summary"]
        update_log = {"guided_by": guide["guided_by"], "phase": guide["phase"], "action": "pending", "accepted": None}

        # Record epoch BEFORE update (policy that produced these metrics)
        epoch_payload = {
            "epoch": t,
            "stamp": stamp,
            "guided_by": guide["guided_by"],
            "phase": guide["phase"],
            "phase_note": guide["note"],
            "policy": policy.to_dict(),
            "metrics": summary,
            "objective": round(_objective(summary, r_floor), 4),
            "r_floor": r_floor,
            "reasoning_traces": [
                {
                    "fixture": r["fixture"],
                    "seed_offset": r["seed_offset"],
                    "C": r["C"],
                    "R": r["R"],
                    "H": r["H"],
                    "anchor_R": r["anchor_R"],
                    "layer_mono": r["layer_mono"],
                    "mid_constraint_R": r["mid_constraint_R"],
                    "path_span_ids": r["path_span_ids"],
                    "typology_path": r["typology_path"],
                    "candidates": r.get("candidates") or [],
                }
                for r in result["rows"]
            ],
            "update": update_log,
            "config": {
                "n_hops": n_hops,
                "seed": seed,
                "n_seeds": n_seeds,
                "n_fixtures": n_fixtures,
                "fixture_ids": [f["id"] for f in fixtures],
            },
        }

        # Update policy for next epoch (still log update into this epoch file)
        if t < n_epochs - 1:
            nxt, upd = update_policy(
                t,
                policy,
                summary,
                history,
                r_floor=r_floor,
                eval_fn=eval_fn,
            )
            epoch_payload["update"] = upd
            # Trim candidates_tried in JSON to summaries only (already small)
            policy = nxt
        else:
            epoch_payload["update"] = {
                "guided_by": guide["guided_by"],
                "phase": guide["phase"],
                "action": "final epoch — no further update",
                "accepted": None,
                "note": guide["note"],
                "candidates_tried": [],
            }

        ep_path = out_dir / f"epoch_{t:02d}.json"
        ep_path.write_text(json.dumps(epoch_payload, indent=2), encoding="utf-8")
        history.append(epoch_payload)
        epoch_summaries.append(
            {
                "epoch": t,
                "guided_by": guide["guided_by"],
                "phase": guide["phase"],
                "avg_C": summary["avg_C"],
                "avg_R": summary["avg_R"],
                "avg_H": summary["avg_H"],
                "avg_anchor_R": summary["avg_anchor_R"],
                "avg_layer_mono": summary["avg_layer_mono"],
                "avg_mid_constraint_R": summary["avg_mid_constraint_R"],
                "policy": epoch_payload["policy"],
                "action": epoch_payload["update"].get("action"),
                "accepted": epoch_payload["update"].get("accepted"),
            }
        )
        print(
            f"epoch {t:02d} [{guide['guided_by']:8s}]  "
            f"C={summary['avg_C']:.3f} R={summary['avg_R']:.3f} H={summary['avg_H']:.3f}  "
            f"mono={summary['avg_layer_mono']:.3f} mid={summary['avg_mid_constraint_R']:.3f}  "
            f"→ {epoch_payload['update'].get('accepted') or epoch_payload['update'].get('action', '')[:48]}"
        )

    best = max(epoch_summaries, key=lambda e: (e["avg_H"], e["avg_R"]))
    trajectory = {
        "stamp": stamp,
        "n_epochs": n_epochs,
        "r_floor": r_floor,
        "epoch_rt_map": EPOCH_RT_MAP,
        "epochs": epoch_summaries,
        "best_epoch": best["epoch"],
        "best_metrics": {
            "avg_C": best["avg_C"],
            "avg_R": best["avg_R"],
            "avg_H": best["avg_H"],
        },
        "best_policy": best["policy"],
        "initial": epoch_summaries[0],
        "final": epoch_summaries[-1],
        "update_rule": {
            "primary": "maximize mean H",
            "constraint": f"soft R floor {r_floor} (quadratic-ish linear penalty)",
            "method": "RT-phased evolutionary / coordinate search over discrete policy variants",
            "not": "no neural / torch training",
        },
    }
    traj_json = out_dir / "trajectory_latest.json"
    traj_json.write_text(json.dumps(trajectory, indent=2), encoding="utf-8")

    # EPOCH_TRAJECTORY.md
    lines = [
        "# Epoch Trajectory (RT-guided iterative training)",
        "",
        f"**Stamp:** {stamp} · **Epochs:** {n_epochs} · **R floor:** {r_floor}",
        "",
        "## Epoch → RT map",
        "",
        "| Epoch | guided_by | phase | note |",
        "| ---: | --- | --- | --- |",
    ]
    for e, g in sorted(EPOCH_RT_MAP.items()):
        if e >= n_epochs:
            continue
        lines.append(f"| {e} | {g['guided_by']} | {g['phase']} | {g['note']} |")
    lines.extend(
        [
            "",
            "## Metrics by epoch",
            "",
            "| epoch | RT | C | R | H | anchor_R | layer_mono | mid_R | accepted |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for e in epoch_summaries:
        lines.append(
            f"| {e['epoch']} | {e['guided_by']} | {e['avg_C']:.3f} | {e['avg_R']:.3f} | "
            f"{e['avg_H']:.3f} | {e['avg_anchor_R']:.3f} | {e['avg_layer_mono']:.3f} | "
            f"{e['avg_mid_constraint_R']:.3f} | {e.get('accepted') or '—'} |"
        )
    lines.extend(
        [
            "",
            f"**Best epoch:** {best['epoch']} (H={best['avg_H']:.3f}, R={best['avg_R']:.3f}, C={best['avg_C']:.3f})",
            "",
            "## Knobs (initial → final → best)",
            "",
            "```json",
            json.dumps(
                {
                    "initial": epoch_summaries[0]["policy"],
                    "final": epoch_summaries[-1]["policy"],
                    "best": best["policy"],
                },
                indent=2,
            ),
            "```",
            "",
            "## Update rule",
            "",
            "- Maximize mean **H** with soft **R** floor.",
            "- Each epoch's search neighborhood is dictated by RT phase (see map).",
            "- Eligible variants evaluated on the same fixtures×seeds; elite kept.",
            "",
        ]
    )
    md_path = out_dir / "EPOCH_TRAJECTORY.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    trajectory["paths"] = {"trajectory_md": str(md_path), "trajectory_json": str(traj_json)}
    return trajectory


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument("--hops", type=int, default=5)
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--seeds", type=int, default=3)
    p.add_argument("--fixtures", type=int, default=4)
    p.add_argument("--r-floor", type=float, default=R_FLOOR_DEFAULT)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=_ROOT / "experiments" / "results" / "iterative_epochs",
    )
    args = p.parse_args(list(argv) if argv is not None else None)
    print("RT-guided iterative reasoning-trace training")
    print("Epoch → RT:", {k: v["guided_by"] for k, v in EPOCH_RT_MAP.items() if k < args.epochs})
    traj = run_training(
        n_epochs=args.epochs,
        n_hops=args.hops,
        seed=args.seed,
        n_seeds=args.seeds,
        n_fixtures=args.fixtures,
        r_floor=args.r_floor,
        out_dir=args.out_dir,
    )
    print("\n=== Best ===")
    print(
        f"epoch {traj['best_epoch']}: "
        f"C={traj['best_metrics']['avg_C']:.3f} "
        f"R={traj['best_metrics']['avg_R']:.3f} "
        f"H={traj['best_metrics']['avg_H']:.3f}"
    )
    print(f"Wrote {traj['paths']['trajectory_md']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
