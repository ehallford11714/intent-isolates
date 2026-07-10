#!/usr/bin/env python3
"""RT8 — Motif–burst hybrid schedule (every k hops force motif_jump then resume burst).

Sweep k ∈ {2,3,4} × motif_weight ∈ {0.45, 0.7} vs motif_jump / elite / convergent.

Success: Some hybrid with H ≥ elite and layer_mono ≥ elite+0.05 and C ≥ elite−0.05.

Usage::

    python experiments/p0_rt8_motif_burst_hybrid.py
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
_EXP = Path(__file__).resolve().parent
for _p in (_SRC, _EXP):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from intentisolates import (  # noqa: E402
    CreativeBurstHopper,
    CreativityMeter,
    identify_span_isolates,
)
from intentisolates.span_burst import filter_spans_for_burst, multi_path_burst  # noqa: E402
from intentisolates.types import BurstHop, BurstPath  # noqa: E402

from theory_corpus_sweep import FIXTURES  # type: ignore  # noqa: E402

ELITE_KNOBS = {
    "anchor_schedule": 2,
    "anchor_pull": 0.80,
    "layer_bias": 0.47,
    "novelty_weight": 1.10,
    "motif_weight": 0.45,
    "side_hop_prob": 0.18,
}


def _typ(v: Any) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _mean(xs: Sequence[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def _prepare_spans(text: str) -> list[Any]:
    spans = identify_span_isolates(text, backend="rule")
    filt = filter_spans_for_burst(spans, drop_noise=True)
    return filt if len(filt) >= 3 else spans


def _hybrid_motif_burst_path(
    spans: Sequence[Any],
    *,
    seed: int,
    n_hops: int,
    every_k: int,
    motif_weight: float,
    seed_index: int = 0,
) -> BurstPath:
    """Every ``every_k`` hops force a motif_jump step, else creative_burst_v2."""
    knobs = {**ELITE_KNOBS, "motif_weight": motif_weight}
    hopper = CreativeBurstHopper.for_v2(spans, seed=seed, **knobs)
    hopper._v2_anchor_explicit = True
    start = hopper.ordered[seed_index % max(1, len(hopper.ordered))]
    rng = random.Random(seed + hash(start.id) % 10_000)
    visited: list[str] = [start.id]
    hops: list[Any] = []
    current = start
    motif_forced = 0

    for step in range(max(0, n_hops)):
        force_motif = every_k > 0 and (step + 1) % every_k == 0
        mode = "motif_jump" if force_motif else "creative_burst_v2"
        nxt, score, reason = hopper._next_hop(current, visited, mode=mode, rng=rng)
        if nxt is None:
            break
        if force_motif:
            motif_forced += 1
            reason = reason + ";motif_schedule"
        hops.append(
            BurstHop(
                from_id=current.id,
                to_id=nxt.id,
                mode=mode,
                score=round(score, 4),
                reason=reason,
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
        mode="motif_burst_hybrid",
        summary=f"every_{every_k}_mw{motif_weight}",
        metadata={
            "every_k": every_k,
            "motif_weight": motif_weight,
            "motif_forced": motif_forced,
        },
    )


def _multipath_hybrid(
    spans: Sequence[Any],
    *,
    seed: int,
    n_hops: int,
    k: int,
    every_k: int,
    motif_weight: float,
    meter: CreativityMeter,
) -> BurstPath:
    best: BurstPath | None = None
    best_h = -1.0
    n_cand = max(1, min(k, len(spans)))
    for i in range(n_cand):
        path = _hybrid_motif_burst_path(
            spans,
            seed=seed + i * 31,
            n_hops=n_hops,
            every_k=every_k,
            motif_weight=motif_weight,
            seed_index=i,
        )
        hopper = CreativeBurstHopper.for_v2(
            spans, seed=seed + i * 31, **{**ELITE_KNOBS, "motif_weight": motif_weight}
        )
        report = meter.score_burst(path, spans, motif_neighbors=hopper._motif_neighbors)
        if report.tradeoff_harmonic > best_h:
            best_h = report.tradeoff_harmonic
            best = path
    assert best is not None
    return best


def run(
    *,
    n_hops: int = 5,
    seed: int = 17,
    n_seeds: int = 5,
    n_fixtures: int = 8,
    k: int = 7,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    out_dir = out_dir or (_ROOT / "experiments" / "results")
    out_dir.mkdir(parents=True, exist_ok=True)
    fixtures = FIXTURES[:n_fixtures]
    meter = CreativityMeter()

    schedules = (0, 2, 3, 4)  # 0 = off (elite burst only)
    weights = (0.45, 0.7)
    conditions: list[str] = ["elite_mpH", "motif_jump", "convergent", "v2_off"]
    for ek in schedules:
        if ek == 0:
            continue
        for mw in weights:
            conditions.append(f"hybrid_every{ek}_mw{mw}")

    rows: list[dict[str, Any]] = []
    by_cond: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for fix in fixtures:
        spans = _prepare_spans(fix["text"])
        if len(spans) < 3:
            continue
        for si in range(n_seeds):
            s = seed + si * 17
            for cond in conditions:
                if cond == "elite_mpH":
                    path, _ = multi_path_burst(
                        spans,
                        n_hops=n_hops,
                        k=k,
                        seed=s,
                        select_by="tradeoff_harmonic",
                        mode="creative_burst_v2",
                        hopper_kwargs=ELITE_KNOBS,
                    )
                    hopper = CreativeBurstHopper.for_v2(spans, seed=s, **ELITE_KNOBS)
                elif cond == "motif_jump":
                    hopper = CreativeBurstHopper(spans, seed=s)
                    path = hopper.burst_path(
                        seed=si % max(1, len(hopper.ordered)),
                        n_hops=n_hops,
                        mode="motif_jump",
                    )
                elif cond == "convergent":
                    hopper = CreativeBurstHopper.for_v2(
                        spans,
                        seed=s,
                        novelty_weight=0.7,
                        anchor_pull=0.95,
                        side_hop_prob=0.05,
                        motif_weight=0.6,
                    )
                    path = hopper.burst_path(
                        seed=si % max(1, len(hopper.ordered)),
                        n_hops=n_hops,
                        mode="creative_burst_v2",
                    )
                elif cond == "v2_off":
                    hopper = CreativeBurstHopper.for_v2(spans, seed=s, **ELITE_KNOBS)
                    path = hopper.burst_path(
                        seed=si % max(1, len(hopper.ordered)),
                        n_hops=n_hops,
                        mode="creative_burst_v2",
                    )
                else:
                    # hybrid_every{k}_mw{w}
                    parts = cond.replace("hybrid_every", "").split("_mw")
                    every_k = int(parts[0])
                    mw = float(parts[1])
                    path = _multipath_hybrid(
                        spans,
                        seed=s,
                        n_hops=n_hops,
                        k=k,
                        every_k=every_k,
                        motif_weight=mw,
                        meter=meter,
                    )
                    hopper = CreativeBurstHopper.for_v2(
                        spans, seed=s, **{**ELITE_KNOBS, "motif_weight": mw}
                    )

                report = meter.score_burst(
                    path, spans, motif_neighbors=hopper._motif_neighbors
                )
                rec = {
                    "fixture": fix["id"],
                    "condition": cond,
                    "seed_offset": si,
                    "C": round(report.creativity_score, 4),
                    "R": round(report.reasoning_trace_score, 4),
                    "H": round(report.tradeoff_harmonic, 4),
                    "anchor_R": round(report.anchor_visit_rate, 4),
                    "layer_mono": round(report.layer_monotonicity, 4),
                    "path_len": len(path.span_ids),
                    "motif_forced": int(path.metadata.get("motif_forced", 0)),
                }
                rows.append(rec)
                by_cond[cond].append(rec)

    summary = []
    for cond in conditions:
        rs = by_cond.get(cond, [])
        summary.append(
            {
                "condition": cond,
                "n": len(rs),
                "avg_C": _mean([r["C"] for r in rs]),
                "avg_R": _mean([r["R"] for r in rs]),
                "avg_H": _mean([r["H"] for r in rs]),
                "avg_anchor_R": _mean([r["anchor_R"] for r in rs]),
                "avg_layer_mono": _mean([r["layer_mono"] for r in rs]),
                "avg_motif_forced": _mean([float(r["motif_forced"]) for r in rs]),
            }
        )
    sm = {s["condition"]: s for s in summary}
    elite = sm["elite_mpH"]
    hybrids = [s for s in summary if s["condition"].startswith("hybrid_")]

    winners = []
    for h in hybrids:
        ok = (
            h["avg_H"] >= elite["avg_H"]
            and h["avg_layer_mono"] >= elite["avg_layer_mono"] + 0.05
            and h["avg_C"] >= elite["avg_C"] - 0.05
        )
        soft = (
            h["avg_H"] >= elite["avg_H"] - 0.01
            and h["avg_layer_mono"] >= elite["avg_layer_mono"] + 0.02
            and h["avg_C"] >= elite["avg_C"] - 0.08
        )
        if ok or soft:
            winners.append({"condition": h["condition"], "strict": ok, **h})

    if any(w["strict"] for w in winners):
        overall = "supported"
    elif winners:
        overall = "mixed"
    else:
        # Best hybrid by H among those with mono lift
        mono_lift = [
            h for h in hybrids if h["avg_layer_mono"] >= elite["avg_layer_mono"] + 0.02
        ]
        overall = "mixed" if mono_lift and any(
            h["avg_C"] >= elite["avg_C"] - 0.08 for h in mono_lift
        ) else "rejected"

    best_hybrid = max(hybrids, key=lambda h: (h["avg_H"], h["avg_layer_mono"])) if hybrids else None

    verdicts = [
        {
            "id": "RT8_motif_burst_hybrid",
            "status": overall,
            "n_winners": len(winners),
            "winners": [w["condition"] for w in winners],
            "best_hybrid": best_hybrid["condition"] if best_hybrid else None,
            "best": (
                {
                    "H": best_hybrid["avg_H"],
                    "C": best_hybrid["avg_C"],
                    "mono": best_hybrid["avg_layer_mono"],
                }
                if best_hybrid
                else None
            ),
            "elite": {
                "H": elite["avg_H"],
                "C": elite["avg_C"],
                "mono": elite["avg_layer_mono"],
            },
            "motif_jump": {
                "H": sm["motif_jump"]["avg_H"],
                "C": sm["motif_jump"]["avg_C"],
                "mono": sm["motif_jump"]["avg_layer_mono"],
            },
        }
    ]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "experiment": "p0_rt8_motif_burst_hybrid",
        "theory_ids": ["RT8", "L1", "P1"],
        "stamp": stamp,
        "config": {
            "n_hops": n_hops,
            "seed": seed,
            "n_seeds": n_seeds,
            "n_fixtures": n_fixtures,
            "k": k,
            "schedules": list(schedules),
            "weights": list(weights),
            "elite_knobs": ELITE_KNOBS,
        },
        "summary_table": summary,
        "verdicts": verdicts,
        "overall_verdict": overall,
        "rows": rows,
    }
    jp = out_dir / f"rt8_motif_burst_hybrid_{stamp}.json"
    latest = out_dir / "rt8_motif_burst_hybrid_latest.json"
    text = json.dumps(payload, indent=2)
    jp.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")

    lines = [
        "# RT8 Motif–Burst Hybrid Schedule",
        "",
        f"**Stamp:** {stamp} · overall=**{overall}** · winners={len(winners)}",
        "",
        "| condition | C | R | H | mono | anchor_R | motif_forced |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in summary:
        lines.append(
            f"| {s['condition']} | {s['avg_C']:.3f} | {s['avg_R']:.3f} | {s['avg_H']:.3f} | "
            f"{s['avg_layer_mono']:.3f} | {s['avg_anchor_R']:.3f} | {s['avg_motif_forced']:.2f} |"
        )
    lines.append("")
    lines.append("## Verdicts")
    for v in verdicts:
        lines.append(
            f"- **{v['id']}**: `{v['status']}` — "
            f"`{json.dumps({kk: v[kk] for kk in v if kk not in ('id', 'status')}, default=str)}`"
        )
    md_path = out_dir / f"rt8_motif_burst_hybrid_{stamp}.md"
    latest_md = out_dir / "rt8_motif_burst_hybrid_latest.md"
    md = "\n".join(lines) + "\n"
    md_path.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        chart_dir = out_dir / "charts"
        chart_dir.mkdir(parents=True, exist_ok=True)
        focus_names = ["elite_mpH", "motif_jump"] + [
            w["condition"] for w in winners[:3]
        ]
        if best_hybrid and best_hybrid["condition"] not in focus_names:
            focus_names.append(best_hybrid["condition"])
        focus = [sm[c] for c in focus_names if c in sm]
        fig, ax = plt.subplots(figsize=(10, 4.5))
        xs = range(len(focus))
        ax.bar([i - 0.2 for i in xs], [s["avg_C"] for s in focus], width=0.2, label="C")
        ax.bar([i for i in xs], [s["avg_H"] for s in focus], width=0.2, label="H")
        ax.bar(
            [i + 0.2 for i in xs],
            [s["avg_layer_mono"] for s in focus],
            width=0.2,
            label="mono",
        )
        ax.set_xticks(list(xs))
        ax.set_xticklabels([s["condition"].replace("_", "\n") for s in focus], fontsize=6)
        ax.set_ylim(0, 1.05)
        ax.legend()
        ax.set_title("RT8 motif–burst hybrids")
        fig.tight_layout()
        cpath = chart_dir / "rt8_motif_burst_hybrid.png"
        fig.savefig(cpath, dpi=120)
        plt.close(fig)
        payload["chart"] = str(cpath)
    except Exception:
        pass

    payload["paths"] = {"json": str(jp), "markdown": str(md_path)}
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hops", type=int, default=5)
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--fixtures", type=int, default=8)
    p.add_argument("--k", type=int, default=7)
    p.add_argument("--out-dir", type=Path, default=_ROOT / "experiments" / "results")
    args = p.parse_args(list(argv) if argv is not None else None)
    payload = run(
        n_hops=args.hops,
        seed=args.seed,
        n_seeds=args.seeds,
        n_fixtures=args.fixtures,
        k=args.k,
        out_dir=args.out_dir,
    )
    print("\n=== RT8 motif-burst hybrid ===")
    print(f"overall={payload['overall_verdict']}")
    for s in payload["summary_table"]:
        if s["condition"] in ("elite_mpH", "motif_jump") or s["condition"].startswith("hybrid_"):
            print(
                f"{s['condition']:28s}  C={s['avg_C']:.3f} H={s['avg_H']:.3f} "
                f"mono={s['avg_layer_mono']:.3f}"
            )
    print(f"\nWrote {payload['paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
