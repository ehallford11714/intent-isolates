#!/usr/bin/env python3
"""P0 follow-up slate: E1 multipath value-fn, E2 protect→burst, E3 structured incubation.

Grounded in COMPILED_EXPERIMENTATION_20260709 + NEXT_EXPERIMENTS_REASONING_TRACE RT1/RT2/RT6.

Usage (from IntentIsolates repo root)::

    python experiments/p0_followup_experiments.py
    python experiments/p0_followup_experiments.py --seeds 5 --hops 5 --incubation-hops 8
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
_EXP = Path(__file__).resolve().parent
for _p in (_SRC, _EXP):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

_RESEARCH = _ROOT.parent
_PD_SRC = _RESEARCH / "PromptDictCompress" / "src"
if _PD_SRC.is_dir() and str(_PD_SRC) not in sys.path:
    sys.path.insert(0, str(_PD_SRC))

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
from intentisolates.types import BurstPath  # noqa: E402

# Reuse fixtures from theory_corpus_sweep
from theory_corpus_sweep import FIXTURES, _scheduled_path  # noqa: E402

_HIGH_VALUE_RE = re.compile(
    r"(?i)\b(goal|constraint|must not|cannot|deadline|budget|require|"
    r"outcome|result|objective|aim to|i want|i need)\b"
)

_PROMPTDICT_NOTE = "unavailable"
try:
    from promptdict.compressor import DictCompressor  # noqa: E402
    from promptdict.metrics import estimate_tokens  # noqa: E402

    _PROMPTDICT_NOTE = "promptdict"
except ImportError:  # pragma: no cover
    DictCompressor = None  # type: ignore
    estimate_tokens = None  # type: ignore


def _typ(v: Any) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _mean(xs: Sequence[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def _path_metrics(
    path: Any,
    spans: Sequence[Any],
    hopper: CreativeBurstHopper,
    meter: CreativityMeter,
) -> dict[str, Any]:
    report = meter.score_burst(path, spans, motif_neighbors=hopper._motif_neighbors)
    return {
        "typology_entropy": typology_path_entropy(path.typology_path),
        "layer_monotonicity": layer_path_monotonicity(spans, path.span_ids),
        "anchor_R": report.anchor_visit_rate,
        "constraint_fidelity": report.constraint_fidelity,
        "C": report.creativity_score,
        "R": report.reasoning_trace_score,
        "H": report.tradeoff_harmonic,
        "path_len": len(path.span_ids),
        "n_spans_pool": len(spans),
        "typology_path": list(path.typology_path),
    }


# ---------------------------------------------------------------------------
# Protect / truncate text transforms (soft PromptDict)
# ---------------------------------------------------------------------------


def _approx_protect_text(text: str, *, budget_tok: int = 400) -> tuple[str, dict[str, Any]]:
    """Keep goal/constraint sentences; drop or compress filler."""
    sentences = re.split(r"(?<=[.!?\n])\s+", text)
    keep: list[str] = []
    rest: list[str] = []
    for s in sentences:
        if _HIGH_VALUE_RE.search(s):
            keep.append(s)
        else:
            rest.append(s)
    keep_blob = " ".join(keep) if keep else text
    rest_blob = " ".join(rest)
    meta: dict[str, Any] = {
        "n_keep": len(keep),
        "n_rest": len(rest),
        "backend": _PROMPTDICT_NOTE,
    }
    if DictCompressor is not None and rest_blob.strip():
        comp = DictCompressor(min_freq=2, max_dict_size=64)
        enc = comp.compress(rest_blob)
        if enc and enc.dictionary:
            visible = keep_blob + "\n<<<COMPACTED>>>\n" + enc.packed_prompt
            if estimate_tokens is not None and estimate_tokens(visible) > budget_tok:
                visible = keep_blob + "\n[filler cold-omitted]"
            meta["tokens_after"] = estimate_tokens(visible) if estimate_tokens else len(visible.split())
            return visible, meta
    # Fallback: protect-only text
    meta["tokens_after"] = len(keep_blob.split())
    return keep_blob, meta


def _truncate_text(text: str, *, keep_frac: float = 0.35) -> tuple[str, dict[str, Any]]:
    """Head/tail truncate to mimic lossy_truncate mid-drop."""
    words = text.split()
    n = len(words)
    keep = max(8, int(n * keep_frac))
    head = keep // 2
    tail = keep - head
    if n <= keep:
        return text, {"tokens_after": n, "mode": "truncate_noop"}
    out = " ".join(words[:head] + ["[...truncated...]"] + words[-tail:])
    return out, {"tokens_after": keep + 1, "mode": "lossy_truncate"}


def _mid_constraint_retention(orig_spans: Sequence[Any], text_after: str) -> float:
    """Fraction of mid-document constraint surfaces still present after compact."""
    mid_cons = [
        s
        for s in orig_spans
        if _typ(s.typology) == "constraint" and getattr(s, "protect", False)
    ]
    if not mid_cons:
        mid_cons = [s for s in orig_spans if _typ(s.typology) == "constraint"]
    if not mid_cons:
        return 1.0
    t = text_after.lower()
    hits = 0
    for s in mid_cons:
        surf = (s.surface or getattr(s, "text", "") or "").strip().lower()
        if not surf:
            continue
        # partial match on distinctive tokens (≥4 chars)
        toks = [w for w in re.findall(r"[a-z0-9]+", surf) if len(w) >= 4]
        if not toks:
            continue
        if sum(1 for w in toks if w in t) / len(toks) >= 0.5:
            hits += 1
    return hits / max(1, len(mid_cons))


def _goal_neglect(path: Any, spans: Sequence[Any]) -> bool:
    by = {s.id: s for s in spans}
    protect_goals = {
        s.id
        for s in spans
        if getattr(s, "protect", False) and _typ(s.typology) in ("goal", "constraint")
    }
    if not protect_goals:
        return False
    visited = set(path.span_ids)
    return not bool(protect_goals & visited)


# ---------------------------------------------------------------------------
# E1 — Multipath value function
# ---------------------------------------------------------------------------

E1_SELECT = (
    ("H", "tradeoff_harmonic"),
    ("R", "reasoning_trace_score"),
    ("C", "creativity_score"),
    ("product", "tradeoff_product"),
    ("iv_diag", "iv_diag"),
)
E1_K = (3, 5, 7)


def run_e1(*, n_hops: int, seed: int, n_seeds: int) -> dict[str, Any]:
    meter = CreativityMeter()
    rows: list[dict[str, Any]] = []
    for fix in FIXTURES:
        spans = identify_span_isolates(fix["text"])
        for k in E1_K:
            for alias, select_by in E1_SELECT:
                cond_id = f"mp_k{k}_{alias}"
                trials = []
                for offset in range(n_seeds):
                    s = seed + offset * 17
                    path, _ = multi_path_burst(
                        spans,
                        n_hops=n_hops,
                        mode="creative_burst_v2",
                        k=k,
                        seed=s,
                        select_by=select_by,
                    )
                    hopper = CreativeBurstHopper.for_v2(spans, seed=s)
                    m = _path_metrics(path, spans, hopper, meter)
                    trials.append(m)
                avg = {
                    k_: _mean([float(t[k_]) for t in trials])
                    for k_ in (
                        "C",
                        "R",
                        "H",
                        "anchor_R",
                        "layer_monotonicity",
                        "typology_entropy",
                        "path_len",
                    )
                }
                rows.append(
                    {
                        "experiment": "E1",
                        "fixture_id": fix["id"],
                        "condition": cond_id,
                        "k": k,
                        "select_by": select_by,
                        "select_alias": alias,
                        "n_seeds": n_seeds,
                        **avg,
                    }
                )

    by_cond: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(r)

    summary = []
    for cond_id in sorted(by_cond):
        rs = by_cond[cond_id]
        summary.append(
            {
                "condition": cond_id,
                "k": rs[0]["k"],
                "select_by": rs[0]["select_by"],
                "select_alias": rs[0]["select_alias"],
                "n": len(rs),
                "avg_C": _mean([r["C"] for r in rs]),
                "avg_R": _mean([r["R"] for r in rs]),
                "avg_H": _mean([r["H"] for r in rs]),
                "avg_anchor_R": _mean([r["anchor_R"] for r in rs]),
                "avg_layer_mono": _mean([r["layer_monotonicity"] for r in rs]),
                "avg_entropy": _mean([r["typology_entropy"] for r in rs]),
            }
        )

    # Hypotheses
    sm = {s["condition"]: s for s in summary}
    hyp: list[dict[str, Any]] = []

    def _h_wins(k: int) -> dict[str, Any]:
        h = sm.get(f"mp_k{k}_H")
        r = sm.get(f"mp_k{k}_R")
        c = sm.get(f"mp_k{k}_C")
        if not (h and r and c):
            return {"id": f"E1_Hmax_k{k}", "verdict": "untested"}
        # H-select wins H among {H,R,C}
        best_h_id = max(
            (f"mp_k{k}_H", f"mp_k{k}_R", f"mp_k{k}_C"),
            key=lambda i: sm[i]["avg_H"],
        )
        # fixture wins: H ≥ R and H ≥ C on H metric
        wins = 0
        total = 0
        for fix in FIXTURES:
            vals = {
                "H": next(
                    (x["H"] for x in rows if x["fixture_id"] == fix["id"] and x["condition"] == f"mp_k{k}_H"),
                    None,
                ),
                "R": next(
                    (x["H"] for x in rows if x["fixture_id"] == fix["id"] and x["condition"] == f"mp_k{k}_R"),
                    None,
                ),
                "C": next(
                    (x["H"] for x in rows if x["fixture_id"] == fix["id"] and x["condition"] == f"mp_k{k}_C"),
                    None,
                ),
            }
            if None in vals.values():
                continue
            total += 1
            if vals["H"] >= vals["R"] - 1e-9 and vals["H"] >= vals["C"] - 1e-9:
                wins += 1
        return {
            "id": f"E1a_selectH_wins_H_k{k}",
            "pred": "select-by-H ≥ select-by-R/C on H",
            "mean_H_by": {"H": h["avg_H"], "R": r["avg_H"], "C": c["avg_H"]},
            "best": best_h_id,
            "fixture_wins": f"{wins}/{total}",
            "verdict": "supported" if best_h_id == f"mp_k{k}_H" else "rejected",
        }

    def _r_wins(k: int) -> dict[str, Any]:
        h = sm.get(f"mp_k{k}_H")
        r = sm.get(f"mp_k{k}_R")
        c = sm.get(f"mp_k{k}_C")
        if not (h and r and c):
            return {"id": f"E1_Rmax_k{k}", "verdict": "untested"}
        best_r = max(
            (f"mp_k{k}_H", f"mp_k{k}_R", f"mp_k{k}_C"),
            key=lambda i: sm[i]["avg_R"],
        )
        return {
            "id": f"E1b_selectR_wins_R_k{k}",
            "pred": "select-by-R ≥ select-by-H/C on R (may cost H)",
            "mean_R_by": {"H": h["avg_R"], "R": r["avg_R"], "C": c["avg_R"]},
            "mean_H_by": {"H": h["avg_H"], "R": r["avg_H"], "C": c["avg_H"]},
            "delta_H_vs_Hselect": round(r["avg_H"] - h["avg_H"], 4),
            "best": best_r,
            "verdict": "supported" if best_r == f"mp_k{k}_R" else "rejected",
        }

    def _g1(k: int) -> dict[str, Any]:
        h = sm.get(f"mp_k{k}_H")
        c = sm.get(f"mp_k{k}_C")
        if not (h and c):
            return {"id": f"E1_G1_k{k}", "verdict": "untested"}
        wins = 0
        for fix in FIXTURES:
            rh = next(
                (x["R"] for x in rows if x["fixture_id"] == fix["id"] and x["condition"] == f"mp_k{k}_H"),
                None,
            )
            rc = next(
                (x["R"] for x in rows if x["fixture_id"] == fix["id"] and x["condition"] == f"mp_k{k}_C"),
                None,
            )
            if rh is None or rc is None:
                continue
            if rh >= rc:
                wins += 1
        return {
            "id": f"E1c_G1_H_vs_C_on_R_k{k}",
            "pred": "select-by-H ≥ select-by-C on R",
            "mean_R": {"H": h["avg_R"], "C": c["avg_R"]},
            "delta": round(h["avg_R"] - c["avg_R"], 4),
            "fixture_wins": f"{wins}/8",
            "verdict": "supported" if h["avg_R"] >= c["avg_R"] else "rejected",
            "strength": "strong" if wins >= 7 else ("moderate" if wins >= 5 else "weak"),
        }

    for k in E1_K:
        hyp.append(_h_wins(k))
        hyp.append(_r_wins(k))
        hyp.append(_g1(k))

    # iv_diag vs H on H and R (k=5 focus)
    for k in (5, 7):
        h = sm.get(f"mp_k{k}_H")
        iv = sm.get(f"mp_k{k}_iv_diag")
        if h and iv:
            hyp.append(
                {
                    "id": f"E1d_iv_diag_vs_H_k{k}",
                    "pred": "iv_diag H ≥ H-select−0.01 and R ≥ H-select R (RT1 success)",
                    "avg_H": {"H": h["avg_H"], "iv_diag": iv["avg_H"]},
                    "avg_R": {"H": h["avg_R"], "iv_diag": iv["avg_R"]},
                    "avg_layer_mono": {"H": h["avg_layer_mono"], "iv_diag": iv["avg_layer_mono"]},
                    "verdict": (
                        "supported"
                        if iv["avg_H"] >= h["avg_H"] - 0.01 and iv["avg_R"] >= h["avg_R"]
                        else "rejected"
                    ),
                }
            )

    return {
        "experiment": "E1",
        "name": "multipath_value_function",
        "n_hops": n_hops,
        "n_seeds": n_seeds,
        "seed": seed,
        "summary_table": summary,
        "rows": rows,
        "hypotheses": hyp,
    }


# ---------------------------------------------------------------------------
# E2 — Protect-compact → burst
# ---------------------------------------------------------------------------


def run_e2(*, n_hops: int, seed: int, n_seeds: int) -> dict[str, Any]:
    meter = CreativityMeter()
    conditions = (
        "raw_v2",
        "truncate_v2",
        "protect_compact_v2",
        "protect_compact_mpH",
    )
    rows: list[dict[str, Any]] = []

    for fix in FIXTURES:
        orig_spans = identify_span_isolates(fix["text"])
        for cond in conditions:
            trials = []
            for offset in range(n_seeds):
                s = seed + offset * 17
                mid_r = 1.0
                neglect = False
                text = fix["text"]
                meta: dict[str, Any] = {}

                if cond.startswith("protect_compact"):
                    text, meta = _approx_protect_text(fix["text"])
                    mid_r = _mid_constraint_retention(orig_spans, text)
                    spans = identify_span_isolates(text)
                    # Prefer protect filter when available; else keep all re-identified
                    filtered = filter_spans_for_burst(spans, drop_noise=True)
                    spans = filtered if len(filtered) >= 3 else spans
                elif cond.startswith("truncate"):
                    text, meta = _truncate_text(fix["text"])
                    mid_r = _mid_constraint_retention(orig_spans, text)
                    spans = identify_span_isolates(text)
                else:
                    spans = list(orig_spans)

                if len(spans) < 2:
                    spans = list(orig_spans)

                if cond.endswith("mpH"):
                    path, _ = multi_path_burst(
                        spans,
                        n_hops=n_hops,
                        mode="creative_burst_v2",
                        k=5,
                        seed=s,
                        select_by="tradeoff_harmonic",
                    )
                    hopper = CreativeBurstHopper.for_v2(spans, seed=s)
                else:
                    hopper = CreativeBurstHopper.for_v2(spans, seed=s)
                    path = hopper.burst_path(
                        seed=offset % max(1, len(hopper.ordered)),
                        n_hops=n_hops,
                        mode="creative_burst_v2",
                    )

                m = _path_metrics(path, spans, hopper, meter)
                neglect = _goal_neglect(path, spans)
                m["mid_constraint_R"] = mid_r
                m["goal_neglect"] = neglect
                m["compact_meta"] = meta
                trials.append(m)

            avg_keys = (
                "C",
                "R",
                "H",
                "anchor_R",
                "layer_monotonicity",
                "typology_entropy",
                "path_len",
                "n_spans_pool",
                "mid_constraint_R",
            )
            avg = {k: _mean([float(t[k]) for t in trials]) for k in avg_keys}
            rows.append(
                {
                    "experiment": "E2",
                    "fixture_id": fix["id"],
                    "condition": cond,
                    "n_seeds": n_seeds,
                    **avg,
                    "goal_neglect_rate": _mean(
                        [1.0 if t["goal_neglect"] else 0.0 for t in trials]
                    ),
                }
            )

    by_cond: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(r)
    summary = []
    for cond in conditions:
        rs = by_cond[cond]
        summary.append(
            {
                "condition": cond,
                "n": len(rs),
                "avg_C": _mean([r["C"] for r in rs]),
                "avg_R": _mean([r["R"] for r in rs]),
                "avg_H": _mean([r["H"] for r in rs]),
                "avg_anchor_R": _mean([r["anchor_R"] for r in rs]),
                "avg_layer_mono": _mean([r["layer_monotonicity"] for r in rs]),
                "avg_mid_constraint_R": _mean([r["mid_constraint_R"] for r in rs]),
                "avg_path_len": _mean([r["path_len"] for r in rs]),
                "avg_pool": _mean([r["n_spans_pool"] for r in rs]),
                "avg_goal_neglect": _mean([r["goal_neglect_rate"] for r in rs]),
            }
        )
    sm = {s["condition"]: s for s in summary}

    hyp = []
    pc = sm["protect_compact_v2"]
    tr = sm["truncate_v2"]
    raw = sm["raw_v2"]
    pc_mp = sm["protect_compact_mpH"]

    hyp.append(
        {
            "id": "E2a_mid_R_protect_vs_truncate",
            "pred": "protect mid_constraint_R ≥ 0.95 and ≫ truncate",
            "protect_mid_R": pc["avg_mid_constraint_R"],
            "truncate_mid_R": tr["avg_mid_constraint_R"],
            "verdict": (
                "supported"
                if pc["avg_mid_constraint_R"] >= 0.95
                and pc["avg_mid_constraint_R"] >= tr["avg_mid_constraint_R"] + 0.3
                else "rejected"
            ),
        }
    )
    hyp.append(
        {
            "id": "E2b_protect_mpH_beats_truncate_on_RH",
            "pred": "protect_compact→multipath_H beats truncate→v2 on R and H",
            "protect_mpH": {"R": pc_mp["avg_R"], "H": pc_mp["avg_H"]},
            "truncate_v2": {"R": tr["avg_R"], "H": tr["avg_H"]},
            "verdict": (
                "supported"
                if pc_mp["avg_R"] >= tr["avg_R"] and pc_mp["avg_H"] >= tr["avg_H"]
                else (
                    "mixed"
                    if (pc_mp["avg_R"] >= tr["avg_R"]) != (pc_mp["avg_H"] >= tr["avg_H"])
                    else "rejected"
                )
            ),
        }
    )
    hyp.append(
        {
            "id": "E2c_protect_v2_near_raw",
            "pred": "protect→v2 R ≥ raw_v2 R − 0.05",
            "protect_R": pc["avg_R"],
            "raw_R": raw["avg_R"],
            "delta": round(pc["avg_R"] - raw["avg_R"], 4),
            "verdict": "supported" if pc["avg_R"] >= raw["avg_R"] - 0.05 else "rejected",
        }
    )
    # Pool-size artifact check: truncate should not fake-win via collapsed pool
    hyp.append(
        {
            "id": "E2d_truncate_not_pool_artifact_winner",
            "pred": "If truncate H>protect H, require comparable pool (±30%); else flag artifact",
            "truncate_H": tr["avg_H"],
            "protect_H": pc["avg_H"],
            "pools": {"truncate": tr["avg_pool"], "protect": pc["avg_pool"], "raw": raw["avg_pool"]},
            "verdict": (
                "artifact_risk"
                if tr["avg_H"] > pc["avg_H"]
                and tr["avg_pool"] < pc["avg_pool"] * 0.7
                else ("ok_no_artifact" if tr["avg_H"] <= pc["avg_H"] else "needs_review")
            ),
        }
    )

    return {
        "experiment": "E2",
        "name": "protect_compact_to_burst",
        "promptdict": _PROMPTDICT_NOTE,
        "n_hops": n_hops,
        "n_seeds": n_seeds,
        "seed": seed,
        "summary_table": summary,
        "rows": rows,
        "hypotheses": hyp,
    }


# ---------------------------------------------------------------------------
# E3 — Structured incubation (strict alt blocks)
# ---------------------------------------------------------------------------


def _structured_incubation_path(
    spans: Sequence[Any],
    *,
    seed: int,
    n_hops: int,
    block: int = 2,
) -> BurstPath:
    """Strict alternate convergent↔divergent every `block` hops (starts divergent)."""
    return _scheduled_path(
        spans,
        seed=seed,
        n_hops=n_hops,
        schedule="incubation",
        base_knobs={},
    )


def run_e3(*, n_hops: int, seed: int, n_seeds: int, incubation_hops: int) -> dict[str, Any]:
    meter = CreativityMeter()
    hop_budgets = sorted({n_hops, incubation_hops, max(6, incubation_hops)})
    conditions_spec = [
        {"id": "creative_burst_v2", "kind": "single"},
        {"id": "multipath_k5_H", "kind": "multipath", "k": 5},
        {"id": "structured_incubation", "kind": "incubation"},
        {"id": "divergent_fixed", "kind": "divergent"},
        {"id": "convergent_fixed", "kind": "convergent"},
    ]
    rows: list[dict[str, Any]] = []

    for hops in hop_budgets:
        for fix in FIXTURES:
            spans = identify_span_isolates(fix["text"])
            for cond in conditions_spec:
                trials = []
                for offset in range(n_seeds):
                    s = seed + offset * 17
                    if cond["kind"] == "multipath":
                        path, _ = multi_path_burst(
                            spans,
                            n_hops=hops,
                            mode="creative_burst_v2",
                            k=int(cond["k"]),
                            seed=s,
                            select_by="tradeoff_harmonic",
                        )
                        hopper = CreativeBurstHopper.for_v2(spans, seed=s)
                    elif cond["kind"] == "incubation":
                        path = _structured_incubation_path(spans, seed=s, n_hops=hops, block=2)
                        hopper = CreativeBurstHopper.for_v2(spans, seed=s)
                    elif cond["kind"] == "divergent":
                        hopper = CreativeBurstHopper.for_v2(
                            spans,
                            seed=s,
                            novelty_weight=1.55,
                            anchor_pull=0.25,
                            anchor_schedule=0,
                            side_hop_prob=0.32,
                            layer_bias=0.2,
                        )
                        path = hopper.burst_path(
                            seed=offset % max(1, len(hopper.ordered)),
                            n_hops=hops,
                            mode="creative_burst_v2",
                        )
                    elif cond["kind"] == "convergent":
                        hopper = CreativeBurstHopper.for_v2(
                            spans,
                            seed=s,
                            novelty_weight=0.7,
                            anchor_pull=0.95,
                            anchor_schedule=2,
                            side_hop_prob=0.05,
                            layer_bias=0.7,
                        )
                        path = hopper.burst_path(
                            seed=offset % max(1, len(hopper.ordered)),
                            n_hops=hops,
                            mode="creative_burst_v2",
                        )
                    else:
                        hopper = CreativeBurstHopper.for_v2(spans, seed=s)
                        path = hopper.burst_path(
                            seed=offset % max(1, len(hopper.ordered)),
                            n_hops=hops,
                            mode="creative_burst_v2",
                        )
                    m = _path_metrics(path, spans, hopper, meter)
                    trials.append(m)
                avg = {
                    k: _mean([float(t[k]) for t in trials])
                    for k in ("C", "R", "H", "anchor_R", "layer_monotonicity", "typology_entropy", "path_len")
                }
                rows.append(
                    {
                        "experiment": "E3",
                        "fixture_id": fix["id"],
                        "condition": cond["id"],
                        "n_hops": hops,
                        "n_seeds": n_seeds,
                        **avg,
                    }
                )

    # Summary per (hops, condition)
    by_key: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_key[(r["n_hops"], r["condition"])].append(r)

    summary = []
    for (hops, cond_id), rs in sorted(by_key.items()):
        summary.append(
            {
                "n_hops": hops,
                "condition": cond_id,
                "n": len(rs),
                "avg_C": _mean([r["C"] for r in rs]),
                "avg_R": _mean([r["R"] for r in rs]),
                "avg_H": _mean([r["H"] for r in rs]),
                "avg_anchor_R": _mean([r["anchor_R"] for r in rs]),
                "avg_layer_mono": _mean([r["layer_monotonicity"] for r in rs]),
                "avg_entropy": _mean([r["typology_entropy"] for r in rs]),
            }
        )

    hyp = []
    for hops in hop_budgets:
        sm = {s["condition"]: s for s in summary if s["n_hops"] == hops}
        inc = sm.get("structured_incubation")
        v2 = sm.get("creative_burst_v2")
        mp = sm.get("multipath_k5_H")
        if not (inc and v2 and mp):
            continue
        # Fixture wins vs v2 on H
        wins_v2 = 0
        wins_mp = 0
        for fix in FIXTURES:
            ih = next(
                (
                    x["H"]
                    for x in rows
                    if x["fixture_id"] == fix["id"]
                    and x["condition"] == "structured_incubation"
                    and x["n_hops"] == hops
                ),
                None,
            )
            vh = next(
                (
                    x["H"]
                    for x in rows
                    if x["fixture_id"] == fix["id"]
                    and x["condition"] == "creative_burst_v2"
                    and x["n_hops"] == hops
                ),
                None,
            )
            mh = next(
                (
                    x["H"]
                    for x in rows
                    if x["fixture_id"] == fix["id"]
                    and x["condition"] == "multipath_k5_H"
                    and x["n_hops"] == hops
                ),
                None,
            )
            if ih is not None and vh is not None and ih >= vh:
                wins_v2 += 1
            if ih is not None and mh is not None and ih >= mh:
                wins_mp += 1
        hyp.append(
            {
                "id": f"E3a_incubation_beats_v2_H_hops{hops}",
                "pred": "structured incubation H ≥ v2_same_hops (≥5/8 fixtures)",
                "mean_H": {"incubation": inc["avg_H"], "v2": v2["avg_H"], "multipath_H": mp["avg_H"]},
                "mean_C": {"incubation": inc["avg_C"], "v2": v2["avg_C"]},
                "fixture_wins_vs_v2": f"{wins_v2}/8",
                "fixture_wins_vs_mp": f"{wins_mp}/8",
                "verdict": "supported" if inc["avg_H"] >= v2["avg_H"] and wins_v2 >= 5 else "rejected",
            }
        )
        hyp.append(
            {
                "id": f"E3b_incubation_vs_multipath_H_hops{hops}",
                "pred": "incubation competitive with multipath_k5_H on H (within 0.01)",
                "delta_H": round(inc["avg_H"] - mp["avg_H"], 4),
                "verdict": (
                    "supported"
                    if inc["avg_H"] >= mp["avg_H"] - 0.01
                    else "rejected"
                ),
            }
        )

    return {
        "experiment": "E3",
        "name": "structured_incubation",
        "hop_budgets": hop_budgets,
        "n_seeds": n_seeds,
        "seed": seed,
        "summary_table": summary,
        "rows": rows,
        "hypotheses": hyp,
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _md_table(rows: list[dict[str, Any]], cols: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(h for h, _ in cols) + " |"
    sep = "| " + " | ".join("---" if not c.startswith("avg_") and c not in ("C", "R", "H", "k", "n") else "---:" for _, c in cols) + " |"
    # simpler: numeric cols right-aligned
    sep_parts = []
    for h, c in cols:
        if c.startswith("avg_") or c in ("k", "n", "n_hops") or h in ("C", "R", "H", "mid_R", "anchor_R", "layer_mono"):
            sep_parts.append("---:")
        else:
            sep_parts.append("---")
    sep = "| " + " | ".join(sep_parts) + " |"
    lines = [header, sep]
    for r in rows:
        cells = []
        for _, key in cols:
            v = r.get(key, "")
            if isinstance(v, float):
                cells.append(f"{v:.3f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_report(payload: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    stamp = payload["stamp"]
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"p0_followup_{stamp}.json"
    md_path = out_dir / f"p0_followup_{stamp}.md"
    latest_json = out_dir / "p0_followup_latest.json"
    latest_md = out_dir / "p0_followup_latest.md"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")

    e1 = payload["E1"]
    e2 = payload["E2"]
    e3 = payload["E3"]

    lines = [
        f"# P0 Follow-up Experiment Results — {stamp}",
        "",
        "Offline slate: **E1** multipath value-function · **E2** protect→burst · **E3** structured incubation.",
        "",
        f"- Fixtures: {len(FIXTURES)} · seeds: {payload['n_seeds']} · base hops: {payload['n_hops']}",
        f"- PromptDict: `{e2.get('promptdict')}`",
        f"- Commands: `python experiments/p0_followup_experiments.py`",
        "",
        "## E1 — Multipath value function",
        "",
        _md_table(
            e1["summary_table"],
            [
                ("condition", "condition"),
                ("k", "k"),
                ("select", "select_alias"),
                ("C", "avg_C"),
                ("R", "avg_R"),
                ("H", "avg_H"),
                ("anchor_R", "avg_anchor_R"),
                ("layer_mono", "avg_layer_mono"),
            ],
        ),
        "",
        "### Hypotheses",
        "",
    ]
    for h in e1["hypotheses"]:
        lines.append(
            f"- **{h['id']}**: `{h.get('verdict')}` — {h.get('pred', '')} "
            f"`{json.dumps({k: v for k, v in h.items() if k not in ('id', 'pred', 'verdict')}, default=str)}`"
        )

    lines += [
        "",
        "## E2 — Protect-compact → burst",
        "",
        _md_table(
            e2["summary_table"],
            [
                ("condition", "condition"),
                ("C", "avg_C"),
                ("R", "avg_R"),
                ("H", "avg_H"),
                ("anchor_R", "avg_anchor_R"),
                ("mid_R", "avg_mid_constraint_R"),
                ("pool", "avg_pool"),
                ("neglect", "avg_goal_neglect"),
            ],
        ),
        "",
        "### Hypotheses",
        "",
    ]
    for h in e2["hypotheses"]:
        lines.append(
            f"- **{h['id']}**: `{h.get('verdict')}` — {h.get('pred', '')} "
            f"`{json.dumps({k: v for k, v in h.items() if k not in ('id', 'pred', 'verdict')}, default=str)}`"
        )

    lines += [
        "",
        "## E3 — Structured incubation",
        "",
        _md_table(
            e3["summary_table"],
            [
                ("hops", "n_hops"),
                ("condition", "condition"),
                ("C", "avg_C"),
                ("R", "avg_R"),
                ("H", "avg_H"),
                ("anchor_R", "avg_anchor_R"),
                ("layer_mono", "avg_layer_mono"),
            ],
        ),
        "",
        "### Hypotheses",
        "",
    ]
    for h in e3["hypotheses"]:
        lines.append(
            f"- **{h['id']}**: `{h.get('verdict')}` — {h.get('pred', '')} "
            f"`{json.dumps({k: v for k, v in h.items() if k not in ('id', 'pred', 'verdict')}, default=str)}`"
        )

    lines += ["", "## Verdict snapshot", "", "| ID | Verdict |", "| --- | --- |"]
    for block in (e1, e2, e3):
        for h in block["hypotheses"]:
            lines.append(f"| {h['id']} | **{h.get('verdict')}** |")
    lines.append("")
    body = "\n".join(lines)

    md_path.write_text(body, encoding="utf-8")
    latest_md.write_text(body, encoding="utf-8")
    return json_path, md_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--hops", type=int, default=5)
    ap.add_argument("--incubation-hops", type=int, default=8)
    ap.add_argument("--seed", type=int, default=17)
    ap.add_argument("--out-dir", type=Path, default=_ROOT / "experiments" / "results")
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print(f"[P0] starting stamp={stamp} seeds={args.seeds} hops={args.hops} incub_hops={args.incubation_hops}")
    print(f"[P0] promptdict={_PROMPTDICT_NOTE}")

    print("[P0] E1 multipath value function...")
    e1 = run_e1(n_hops=args.hops, seed=args.seed, n_seeds=args.seeds)
    print(f"  conditions={len(e1['summary_table'])}")

    print("[P0] E2 protect->burst...")
    e2 = run_e2(n_hops=args.hops, seed=args.seed, n_seeds=args.seeds)
    print(f"  conditions={len(e2['summary_table'])}")

    print("[P0] E3 structured incubation...")
    e3 = run_e3(
        n_hops=args.hops,
        seed=args.seed,
        n_seeds=args.seeds,
        incubation_hops=args.incubation_hops,
    )
    print(f"  conditions={len(e3['summary_table'])}")

    payload = {
        "stamp": stamp,
        "n_seeds": args.seeds,
        "n_hops": args.hops,
        "incubation_hops": args.incubation_hops,
        "seed": args.seed,
        "fixtures": [f["id"] for f in FIXTURES],
        "E1": e1,
        "E2": e2,
        "E3": e3,
    }
    jp, mp = write_report(payload, args.out_dir)
    print(f"[P0] wrote {jp}")
    print(f"[P0] wrote {mp}")

    # quick console tables
    print("\n=== E1 summary (H top) ===")
    for s in sorted(e1["summary_table"], key=lambda x: -x["avg_H"])[:8]:
        print(f"  {s['condition']:20s} C={s['avg_C']:.3f} R={s['avg_R']:.3f} H={s['avg_H']:.3f}")
    print("\n=== E2 summary ===")
    for s in e2["summary_table"]:
        print(
            f"  {s['condition']:24s} C={s['avg_C']:.3f} R={s['avg_R']:.3f} H={s['avg_H']:.3f} "
            f"midR={s['avg_mid_constraint_R']:.3f}"
        )
    print("\n=== E3 summary (by hops) ===")
    for s in e3["summary_table"]:
        print(
            f"  hops={s['n_hops']} {s['condition']:24s} "
            f"C={s['avg_C']:.3f} R={s['avg_R']:.3f} H={s['avg_H']:.3f}"
        )
    print("\n=== Hypotheses ===")
    for block in (e1, e2, e3):
        for h in block["hypotheses"]:
            print(f"  {h['id']}: {h.get('verdict')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
