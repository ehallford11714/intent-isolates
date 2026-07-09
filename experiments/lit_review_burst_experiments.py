#!/usr/bin/env python3
"""Lit-review grounded burst experiments + CreativityMeter scoring.

Maps creativity / reasoning literature constructs onto hop conditions and
compares them offline on C, R, tradeoff, entropy, anchor_R, layer monotonicity.

Usage (from IntentIsolates repo root)::

    python experiments/lit_review_burst_experiments.py
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
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
    layer_path_monotonicity,
    multi_path_burst,
    typology_path_entropy,
)

# Reuse fixtures from span_burst_creative when available
sys.path.insert(0, str(_ROOT / "experiments"))
try:
    from span_burst_creative import FIXTURES  # type: ignore
except ImportError:
    FIXTURES = [
        {
            "id": "product_metaphor",
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
    ]

# Lit construct → hop condition
CONDITIONS: list[dict[str, Any]] = [
    {
        "id": "linear",
        "lit": "document-order baseline (no divergent search)",
        "mode": "linear",
        "knobs": {},
    },
    {
        "id": "random",
        "lit": "unconstrained exploration baseline",
        "mode": "random",
        "knobs": {},
    },
    {
        "id": "motif_jump",
        "lit": "Mednick associative / motif-guided search",
        "mode": "motif_jump",
        "knobs": {},
    },
    {
        "id": "creative_burst_v1",
        "lit": "prior creative_burst (soft anchor + novelty)",
        "mode": "creative_burst",
        "knobs": {"anchor_pull": 0.55},
    },
    {
        "id": "divergent_guilford",
        "lit": "Guilford divergent: maximize novelty/entropy/fluency",
        "mode": "creative_burst_v2",
        "knobs": {
            "novelty_weight": 1.6,
            "anchor_pull": 0.25,
            "anchor_schedule": 0,
            "layer_bias": 0.15,
            "motif_weight": 0.20,
            "side_hop_prob": 0.35,
        },
    },
    {
        "id": "convergent_constrained",
        "lit": "Constrained / convergent creativity: high anchor schedule",
        "mode": "creative_burst_v2",
        "knobs": {
            "novelty_weight": 0.6,
            "anchor_pull": 1.0,
            "anchor_schedule": 2,
            "layer_bias": 0.45,
            "motif_weight": 0.50,
            "side_hop_prob": 0.05,
        },
    },
    {
        "id": "novelty_boden",
        "lit": "Boden exploratory: high novelty_weight within space",
        "mode": "creative_burst_v2",
        "knobs": {
            "novelty_weight": 1.45,
            "anchor_pull": 0.55,
            "anchor_schedule": 4,
            "layer_bias": 0.35,
            "motif_weight": 0.35,
            "side_hop_prob": 0.25,
        },
    },
    {
        "id": "layer_cot",
        "lit": "CoT scaffolding: forward layer_bias",
        "mode": "creative_burst_v2",
        "knobs": {
            "novelty_weight": 0.9,
            "anchor_pull": 0.65,
            "anchor_schedule": 3,
            "layer_bias": 0.95,
            "motif_weight": 0.40,
            "side_hop_prob": 0.08,
        },
    },
    {
        "id": "creative_burst_v2",
        "lit": "P0 hybrid: novelty+motif+anchor+layer (recommended defaults)",
        "mode": "creative_burst_v2",
        "knobs": {},  # for_v2 defaults
        "use_for_v2": True,
    },
    {
        "id": "multipath_tot",
        "lit": "ToT/GoT: k paths, select by CreativityMeter harmonic C&R",
        "mode": "creative_burst_v2",
        "knobs": {},
        "multi_path": True,
        "k": 5,
        "select_by": "tradeoff_harmonic",
        "use_for_v2": True,
    },
]


def _typ(v: Any) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _mean(xs: Sequence[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def _make_hopper(spans: Sequence[Any], seed: int, cond: dict[str, Any]) -> CreativeBurstHopper:
    knobs = dict(cond.get("knobs") or {})
    if cond.get("use_for_v2") and not knobs:
        return CreativeBurstHopper.for_v2(spans, seed=seed)
    if cond["mode"] == "creative_burst_v2":
        return CreativeBurstHopper.for_v2(spans, seed=seed, **knobs)
    return CreativeBurstHopper(spans, seed=seed, **{k: v for k, v in knobs.items() if k == "anchor_pull"})


def _path_metrics(path: Any, spans: Sequence[Any], hopper: CreativeBurstHopper, meter: CreativityMeter) -> dict[str, Any]:
    report = meter.score_burst(path, spans, motif_neighbors=hopper._motif_neighbors)
    by_id = {s.id: s for s in spans}
    goal_c = sum(1 for i in path.span_ids if i in by_id and _typ(by_id[i].typology) == "goal")
    cons_c = sum(1 for i in path.span_ids if i in by_id and _typ(by_id[i].typology) == "constraint")
    return {
        "typology_entropy": typology_path_entropy(path.typology_path),
        "n_unique_typologies": len(set(path.typology_path)),
        "layer_monotonicity": layer_path_monotonicity(spans, path.span_ids),
        "anchor_R": report.anchor_visit_rate,
        "goal_visits": goal_c,
        "constraint_visits": cons_c,
        "diversity": report.diversity,
        "novelty": report.novelty,
        "flexibility": report.flexibility,
        "elaboration": report.elaboration,
        "fluency": report.fluency,
        "constraint_fidelity": report.constraint_fidelity,
        "C": report.creativity_score,
        "R": report.reasoning_trace_score,
        "CxR": report.tradeoff_product,
        "H": report.tradeoff_harmonic,
        "path_len": len(path.span_ids),
        "typology_path": list(path.typology_path),
    }


def run(*, n_hops: int, seed: int, out_dir: Path) -> dict[str, Any]:
    meter = CreativityMeter()
    rows: list[dict[str, Any]] = []

    for fix in FIXTURES:
        spans = identify_span_isolates(fix["text"])
        for cond in CONDITIONS:
            trial_metrics: list[dict[str, Any]] = []
            for offset in range(3):
                s = seed + offset * 17
                if cond.get("multi_path"):
                    hopper = _make_hopper(spans, s, cond)
                    path, _cands = multi_path_burst(
                        spans,
                        n_hops=n_hops,
                        mode=cond["mode"],
                        k=int(cond.get("k", 5)),
                        seed=s,
                        select_by=str(cond.get("select_by", "tradeoff_harmonic")),
                        hopper_kwargs=cond.get("knobs") or None,
                    )
                    # Rebuild hopper for neighbor map
                    hopper = _make_hopper(spans, s, cond)
                else:
                    hopper = _make_hopper(spans, s, cond)
                    path = hopper.burst_path(seed=offset, n_hops=n_hops, mode=cond["mode"])
                trial_metrics.append(_path_metrics(path, spans, hopper, meter))

            avg_keys = [
                "typology_entropy",
                "n_unique_typologies",
                "layer_monotonicity",
                "anchor_R",
                "goal_visits",
                "constraint_visits",
                "diversity",
                "novelty",
                "flexibility",
                "elaboration",
                "fluency",
                "constraint_fidelity",
                "C",
                "R",
                "CxR",
                "H",
                "path_len",
            ]
            avg = {k: _mean([float(m[k]) for m in trial_metrics]) for k in avg_keys}
            rows.append(
                {
                    "fixture_id": fix["id"],
                    "condition": cond["id"],
                    "lit": cond["lit"],
                    "mode": cond["mode"],
                    "n_spans": len(spans),
                    **avg,
                    "example_typology_path": trial_metrics[0]["typology_path"],
                }
            )

    by_cond: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(r)

    summary = []
    for cond in CONDITIONS:
        rs = by_cond[cond["id"]]
        summary.append(
            {
                "condition": cond["id"],
                "lit": cond["lit"],
                "mode": cond["mode"],
                "n": len(rs),
                "avg_C": _mean([r["C"] for r in rs]),
                "avg_R": _mean([r["R"] for r in rs]),
                "avg_H": _mean([r["H"] for r in rs]),
                "avg_CxR": _mean([r["CxR"] for r in rs]),
                "avg_entropy": _mean([r["typology_entropy"] for r in rs]),
                "avg_anchor_R": _mean([r["anchor_R"] for r in rs]),
                "avg_layer_mono": _mean([r["layer_monotonicity"] for r in rs]),
                "avg_diversity": _mean([r["diversity"] for r in rs]),
                "avg_novelty": _mean([r["novelty"] for r in rs]),
                "avg_flexibility": _mean([r["flexibility"] for r in rs]),
                "avg_unique_typs": _mean([r["n_unique_typologies"] for r in rs]),
            }
        )

    sm = {s["condition"]: s for s in summary}
    v2 = sm.get("creative_burst_v2", {})
    v1 = sm.get("creative_burst_v1", {})
    rnd = sm.get("random", {})
    mp = sm.get("multipath_tot", {})
    conv = sm.get("convergent_constrained", {})
    div = sm.get("divergent_guilford", {})

    verdict: list[str] = []
    if (v2.get("avg_R") or 0) > (v1.get("avg_R") or 0):
        verdict.append(
            f"creative_burst_v2 improved R vs v1 ({v2.get('avg_R'):.3f} > {v1.get('avg_R'):.3f})."
        )
    else:
        verdict.append(
            f"creative_burst_v2 R ({v2.get('avg_R')}) did not beat v1 ({v1.get('avg_R')}); inspect knobs."
        )
    if (v2.get("avg_H") or 0) >= (rnd.get("avg_H") or 0):
        verdict.append(
            f"v2 harmonic tradeoff H>=random ({v2.get('avg_H'):.3f} >= {rnd.get('avg_H'):.3f})."
        )
    if (mp.get("avg_H") or 0) >= (v2.get("avg_H") or 0):
        verdict.append(
            f"ToT multi-path select-by-meter matched/beat single v2 on H "
            f"({mp.get('avg_H'):.3f} >= {v2.get('avg_H'):.3f})."
        )
    else:
        verdict.append(
            f"Single-path v2 H ({v2.get('avg_H')}) beat multi-path ({mp.get('avg_H')}) - "
            "selection may need more seeds or different objective."
        )
    if (conv.get("avg_anchor_R") or 0) >= (div.get("avg_anchor_R") or 0):
        verdict.append(
            "Convergent/constrained condition preserved anchors >= divergent (as lit predicts)."
        )
    if (div.get("avg_entropy") or 0) >= (conv.get("avg_entropy") or 0):
        verdict.append(
            "Divergent condition entropy >= convergent (Guilford fluency/flexibility proxy)."
        )

    # Rank by harmonic tradeoff
    ranked = sorted(summary, key=lambda s: (-s["avg_H"], -s["avg_R"], -s["avg_C"]))
    verdict.append(
        "Best H (C&R): "
        + ", ".join(f"{s['condition']}={s['avg_H']:.3f}" for s in ranked[:3])
    )

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "backend": "intentisolates",
        "n_hops": n_hops,
        "seed": seed,
        "n_fixtures": len(FIXTURES),
        "conditions": [c["id"] for c in CONDITIONS],
        "lit_mapping": [{k: c[k] for k in ("id", "lit", "mode")} for c in CONDITIONS],
        "summary_table": summary,
        "ranked_by_H": [s["condition"] for s in ranked],
        "rows": rows,
        "verdict": verdict,
        "hypothesis": (
            "Lit-grounded hop policies: divergent raises C/entropy; constrained raises R/anchors; "
            "v2 hybrid and ToT multi-path improve harmonic tradeoff vs random/linear."
        ),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"lit_burst_{stamp}.json"
    md_path = out_dir / f"lit_burst_{stamp}.md"
    latest_json = out_dir / "lit_burst_latest.json"
    latest_md = out_dir / "lit_burst_latest.md"
    text = json.dumps(payload, indent=2)
    json_path.write_text(text, encoding="utf-8")
    latest_json.write_text(text, encoding="utf-8")
    md = _render_md(payload)
    md_path.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")
    payload["paths"] = {
        "json": str(json_path),
        "markdown": str(md_path),
        "latest_json": str(latest_json),
        "latest_md": str(latest_md),
    }
    return payload


def _render_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Lit-review grounded burst experiments",
        "",
        f"- Created: `{payload['created_at']}`",
        f"- Hops: `{payload['n_hops']}` · fixtures: `{payload['n_fixtures']}`".replace("·", "-"),
        "",
        "## Lit → condition mapping",
        "",
        "| condition | lit idea | mode |",
        "| --- | --- | --- |",
    ]
    for m in payload["lit_mapping"]:
        lines.append(f"| {m['id']} | {m['lit']} | `{m['mode']}` |")
    lines += [
        "",
        "## Summary (CreativityMeter)",
        "",
        "| condition | C | R | H | CxR | entropy | anchor_R | layer_mono | novelty | flex |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in payload["summary_table"]:
        lines.append(
            f"| {s['condition']} | {s['avg_C']:.3f} | {s['avg_R']:.3f} | {s['avg_H']:.3f} | "
            f"{s['avg_CxR']:.3f} | {s['avg_entropy']:.3f} | {s['avg_anchor_R']:.3f} | "
            f"{s['avg_layer_mono']:.3f} | {s['avg_novelty']:.3f} | {s['avg_flexibility']:.3f} |"
        )
    lines += ["", "## Ranked by harmonic H (C&R)", ""]
    for i, name in enumerate(payload["ranked_by_H"], 1):
        lines.append(f"{i}. `{name}`")
    lines += ["", "## Verdict", ""]
    for v in payload["verdict"]:
        lines.append(f"- {v}")
    lines += ["", "## Hypothesis", "", payload["hypothesis"], ""]
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hops", type=int, default=5)
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--out-dir", type=Path, default=_ROOT / "experiments" / "results")
    args = p.parse_args(list(argv) if argv is not None else None)
    payload = run(n_hops=args.hops, seed=args.seed, out_dir=args.out_dir)
    print("\n=== Lit-burst summary (C / R / H) ===")
    for s in payload["summary_table"]:
        print(
            f"{s['condition']:24s}  C={s['avg_C']:.3f}  R={s['avg_R']:.3f}  "
            f"H={s['avg_H']:.3f}  ent={s['avg_entropy']:.3f}  "
            f"anchor_R={s['avg_anchor_R']:.3f}  mono={s['avg_layer_mono']:.3f}"
        )
    print("\nVerdict:")
    for v in payload["verdict"]:
        print(f"  - {v}")
    print(f"\nWrote {payload['paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
