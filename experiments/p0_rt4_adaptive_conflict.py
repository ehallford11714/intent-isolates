#!/usr/bin/env python3
"""RT4 adaptive: conflict/thrash-triggered schedule vs fixed schedule=2 elite.

Compares:
  - elite_fixed_s2: multipath k=7 select_by=H, protect on, schedule=2, pull≈0.80
  - stock_v2_s3: schedule=3, pull=0.70 (v2 defaults)
  - adaptive_thrash: schedule=3 baseline; drop to schedule=2 when typology thrash high
  - adaptive_grid: threshold variants
  - hybrid_interrupt: schedule=3 with one forced conflict interrupt mid-path

Goal: recover C while keeping H/R gains of schedule=2.

Usage::

    python experiments/p0_rt4_adaptive_conflict.py
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
_EXP = Path(__file__).resolve().parent
for _p in (_SRC, _EXP):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from intentisolates import (  # noqa: E402
    CreativeBurstHopper,
    CreativityMeter,
    identify_span_isolates,
)
from intentisolates.span_burst import (  # noqa: E402
    filter_spans_for_burst,
    multi_path_burst,
    typology_path_entropy,
)
from intentisolates.types import BurstPath  # noqa: E402

from theory_corpus_sweep import FIXTURES  # type: ignore  # noqa: E402


def _typ(v: Any) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _mean(xs: Sequence[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def _thrash_score(typology_path: Sequence[str]) -> float:
    """Fraction of consecutive hops that change typology (conflict/thrash proxy)."""
    if len(typology_path) < 2:
        return 0.0
    flips = sum(1 for a, b in zip(typology_path, typology_path[1:]) if a != b)
    return flips / (len(typology_path) - 1)


def _prepare_spans(text: str, *, protect: bool) -> list[Any]:
    spans = identify_span_isolates(text, backend="rule")
    if protect:
        filt = filter_spans_for_burst(spans, drop_noise=True)
        if len(filt) >= 3:
            return filt
    return spans


def _continuous_adaptive_path(
    spans: Sequence[Any],
    *,
    seed: int,
    n_hops: int,
    thrash_threshold: float,
    pull_hi: float = 0.80,
    pull_lo: float = 0.70,
    layer_bias: float = 0.47,
    seed_index: int = 0,
) -> tuple[BurstPath, dict[str, Any]]:
    """Single continuous burst; switch schedule/pull mid-path on thrash/low anchors.

    Starts at schedule=3 / pull_lo (stock-like C). After ≥2 hops, if typology thrash
    or missing protect visits, tightens to schedule=2 / pull_hi for remaining hops.
    """
    import random as _random

    from intentisolates.types import BurstHop

    hopper = CreativeBurstHopper.for_v2(
        spans,
        seed=seed,
        anchor_schedule=3,
        anchor_pull=pull_lo,
        layer_bias=layer_bias,
    )
    start = hopper.ordered[seed_index % max(1, len(hopper.ordered))]
    rng = _random.Random(seed + hash(start.id) % 10_000)
    visited: list[str] = [start.id]
    hops: list[Any] = []
    current = start
    triggered = False
    trigger_at: int | None = None
    anchors = {s.id for s in spans if getattr(s, "protect", False)}

    for step in range(max(0, n_hops)):
        # Evaluate thrash on path so far (after ≥2 nodes)
        if not triggered and len(visited) >= 3:
            typs = [_typ(hopper.by_id[i].typology) for i in visited if i in hopper.by_id]
            thrash = _thrash_score(typs)
            visited_anchors = sum(1 for a in anchors if a in set(visited))
            low_anchor = visited_anchors == 0
            if thrash >= thrash_threshold or low_anchor:
                hopper.anchor_schedule = 2
                hopper.anchor_pull = pull_hi
                hopper._v2_anchor_explicit = True
                triggered = True
                trigger_at = step

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
                reason=reason + (";conflict_adapt" if triggered else ""),
            )
        )
        visited.append(nxt.id)
        current = nxt

    typ_path = [_typ(hopper.by_id[i].typology) for i in visited if i in hopper.by_id]
    path = BurstPath(
        seed_id=start.id,
        hops=hops,
        span_ids=visited,
        typology_path=typ_path,
        mode="creative_burst_v2",
        summary="adaptive_thrash",
        metadata={
            "triggered": triggered,
            "trigger_at": trigger_at,
            "thrash_threshold": thrash_threshold,
            "final_schedule": hopper.anchor_schedule,
            "final_pull": hopper.anchor_pull,
        },
    )
    meta = {
        "triggered": triggered,
        "thrash": round(_thrash_score(typ_path), 4),
        "trigger_at": trigger_at,
        "phase2_schedule": 2 if triggered else 3,
    }
    return path, meta


def _hybrid_interrupt_path(
    spans: Sequence[Any],
    *,
    seed: int,
    n_hops: int,
    layer_bias: float = 0.47,
    seed_index: int = 0,
) -> BurstPath:
    """Continuous path: schedule=3, force schedule=2 for exactly one mid hop."""
    import random as _random

    from intentisolates.types import BurstHop

    hopper = CreativeBurstHopper.for_v2(
        spans,
        seed=seed,
        anchor_schedule=3,
        anchor_pull=0.70,
        layer_bias=layer_bias,
    )
    start = hopper.ordered[seed_index % max(1, len(hopper.ordered))]
    rng = _random.Random(seed + hash(start.id) % 10_000)
    visited: list[str] = [start.id]
    hops: list[Any] = []
    current = start
    interrupt_at = max(1, n_hops // 2)

    for step in range(max(0, n_hops)):
        if step == interrupt_at:
            hopper.anchor_schedule = 2
            hopper.anchor_pull = 0.85
            hopper._v2_anchor_explicit = True
        elif step == interrupt_at + 1:
            hopper.anchor_schedule = 3
            hopper.anchor_pull = 0.70
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
        mode="creative_burst_v2",
        summary="hybrid_interrupt",
        metadata={"interrupt_at": interrupt_at},
    )


def _multipath_adaptive(
    spans: Sequence[Any],
    *,
    seed: int,
    n_hops: int,
    k: int,
    thrash_threshold: float,
    meter: CreativityMeter,
) -> tuple[BurstPath, dict[str, Any]]:
    """k adaptive candidates; select by H (fair vs elite multipath)."""
    best_path: BurstPath | None = None
    best_h = -1.0
    best_meta: dict[str, Any] = {}
    n_trig = 0
    n_cand = max(1, min(k, len(spans)))
    for i in range(n_cand):
        path, meta = _continuous_adaptive_path(
            spans,
            seed=seed + i * 31,
            n_hops=n_hops,
            thrash_threshold=thrash_threshold,
            seed_index=i,
        )
        if meta.get("triggered"):
            n_trig += 1
        hopper = CreativeBurstHopper.for_v2(spans, seed=seed + i * 31)
        report = meter.score_burst(path, spans, motif_neighbors=hopper._motif_neighbors)
        if report.tradeoff_harmonic > best_h:
            best_h = report.tradeoff_harmonic
            best_path = path
            best_meta = dict(meta)
    assert best_path is not None
    best_meta["trigger_rate_among_k"] = n_trig / n_cand
    return best_path, best_meta


def _multipath_hybrid(
    spans: Sequence[Any],
    *,
    seed: int,
    n_hops: int,
    k: int,
    meter: CreativityMeter,
) -> BurstPath:
    best_path: BurstPath | None = None
    best_h = -1.0
    n_cand = max(1, min(k, len(spans)))
    for i in range(n_cand):
        path = _hybrid_interrupt_path(
            spans, seed=seed + i * 31, n_hops=n_hops, seed_index=i
        )
        hopper = CreativeBurstHopper.for_v2(spans, seed=seed + i * 31)
        report = meter.score_burst(path, spans, motif_neighbors=hopper._motif_neighbors)
        if report.tradeoff_harmonic > best_h:
            best_h = report.tradeoff_harmonic
            best_path = path
    assert best_path is not None
    return best_path


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

    # Elite from iterative report
    elite_knobs = {
        "anchor_schedule": 2,
        "anchor_pull": 0.80,
        "layer_bias": 0.47,
        "novelty_weight": 1.10,
        "motif_weight": 0.45,
        "side_hop_prob": 0.18,
    }
    stock_knobs = {
        "anchor_schedule": 3,
        "anchor_pull": 0.70,
        "layer_bias": 0.55,
    }

    conditions = (
        "elite_fixed_s2_mpH",
        "stock_v2_s3_mpH",
        "adaptive_thrash_0.55",
        "adaptive_thrash_0.70",
        "adaptive_thrash_0.40",
        "hybrid_interrupt",
        "fixed_s2_single",
        "stock_v2_s3_single",
    )

    rows: list[dict[str, Any]] = []
    by_cond: dict[str, list[dict[str, Any]]] = defaultdict(list)
    trigger_rates: dict[str, list[float]] = defaultdict(list)

    for fix in fixtures:
        spans_prot = _prepare_spans(fix["text"], protect=True)
        spans_raw = _prepare_spans(fix["text"], protect=False)
        if len(spans_prot) < 3:
            continue

        for si in range(n_seeds):
            s = seed + si * 17
            for cond in conditions:
                meta: dict[str, Any] = {}
                use_prot = cond.startswith("elite") or cond.startswith("adaptive") or cond.startswith(
                    "hybrid"
                ) or cond.startswith("fixed_s2")
                spans = spans_prot if use_prot else spans_raw

                if cond == "elite_fixed_s2_mpH":
                    path, _ = multi_path_burst(
                        spans,
                        n_hops=n_hops,
                        k=k,
                        seed=s,
                        select_by="tradeoff_harmonic",
                        mode="creative_burst_v2",
                        hopper_kwargs=elite_knobs,
                    )
                    hopper = CreativeBurstHopper.for_v2(spans, seed=s, **elite_knobs)
                elif cond == "stock_v2_s3_mpH":
                    path, _ = multi_path_burst(
                        spans,
                        n_hops=n_hops,
                        k=k,
                        seed=s,
                        select_by="tradeoff_harmonic",
                        mode="creative_burst_v2",
                        hopper_kwargs=stock_knobs,
                    )
                    hopper = CreativeBurstHopper.for_v2(spans, seed=s, **stock_knobs)
                elif cond.startswith("adaptive_thrash_"):
                    thr = float(cond.rsplit("_", 1)[-1])
                    path, meta = _multipath_adaptive(
                        spans,
                        seed=s,
                        n_hops=n_hops,
                        k=k,
                        thrash_threshold=thr,
                        meter=meter,
                    )
                    hopper = CreativeBurstHopper.for_v2(spans, seed=s, **elite_knobs)
                    trigger_rates[cond].append(1.0 if meta.get("triggered") else 0.0)
                elif cond == "hybrid_interrupt":
                    path = _multipath_hybrid(
                        spans, seed=s, n_hops=n_hops, k=k, meter=meter
                    )
                    hopper = CreativeBurstHopper.for_v2(spans, seed=s, **stock_knobs)
                elif cond == "fixed_s2_single":
                    hopper = CreativeBurstHopper.for_v2(spans, seed=s, **elite_knobs)
                    path = hopper.burst_path(
                        seed=si % max(1, len(hopper.ordered)),
                        n_hops=n_hops,
                        mode="creative_burst_v2",
                    )
                else:  # stock_v2_s3_single
                    hopper = CreativeBurstHopper.for_v2(spans, seed=s, **stock_knobs)
                    path = hopper.burst_path(
                        seed=si % max(1, len(hopper.ordered)),
                        n_hops=n_hops,
                        mode="creative_burst_v2",
                    )

                report = meter.score_burst(
                    path, spans, motif_neighbors=hopper._motif_neighbors
                )
                thrash = _thrash_score(path.typology_path)
                rec = {
                    "fixture": fix["id"],
                    "condition": cond,
                    "seed_offset": si,
                    "C": round(report.creativity_score, 4),
                    "R": round(report.reasoning_trace_score, 4),
                    "H": round(report.tradeoff_harmonic, 4),
                    "anchor_R": round(report.anchor_visit_rate, 4),
                    "layer_mono": round(report.layer_monotonicity, 4),
                    "thrash": round(thrash, 4),
                    "entropy": typology_path_entropy(path.typology_path),
                    "path_len": len(path.span_ids),
                    "triggered": bool(meta.get("triggered", False)),
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
                "avg_thrash": _mean([r["thrash"] for r in rs]),
                "trigger_rate": _mean(trigger_rates.get(cond, [0.0])),
            }
        )
    sm = {s["condition"]: s for s in summary}
    elite = sm["elite_fixed_s2_mpH"]
    stock = sm["stock_v2_s3_mpH"]

    # Per-fixture adaptive vs elite / stock
    fixture_ids = sorted({r["fixture"] for r in rows})
    best_adaptive_name = max(
        (c for c in conditions if c.startswith("adaptive_thrash_")),
        key=lambda c: sm[c]["avg_H"],
    )
    adapt = sm[best_adaptive_name]
    hybrid = sm["hybrid_interrupt"]

    def _fixture_means(cond: str) -> dict[str, dict[str, float]]:
        out: dict[str, dict[str, float]] = {}
        for fx in fixture_ids:
            rs = [r for r in rows if r["fixture"] == fx and r["condition"] == cond]
            if not rs:
                continue
            out[fx] = {
                "C": _mean([r["C"] for r in rs]),
                "R": _mean([r["R"] for r in rs]),
                "H": _mean([r["H"] for r in rs]),
            }
        return out

    elite_fx = _fixture_means("elite_fixed_s2_mpH")
    adapt_fx = _fixture_means(best_adaptive_name)
    stock_fx = _fixture_means("stock_v2_s3_mpH")

    # Success: Adaptive H ≥ schedule_2 − 0.005 and C ≥ v2 − 0.03 on ≥6/8 fixtures
    n_ok = 0
    per_fx = []
    for fx in fixture_ids:
        if fx not in adapt_fx or fx not in elite_fx or fx not in stock_fx:
            continue
        a, e, st = adapt_fx[fx], elite_fx[fx], stock_fx[fx]
        ok = a["H"] >= e["H"] - 0.005 and a["C"] >= st["C"] - 0.03
        # Also count soft: H within 0.01 of elite and C > elite
        soft = a["H"] >= e["H"] - 0.01 and a["C"] >= e["C"]
        if ok or soft:
            n_ok += 1
        per_fx.append(
            {
                "fixture": fx,
                "ok": ok or soft,
                "strict": ok,
                "adapt_H": a["H"],
                "elite_H": e["H"],
                "adapt_C": a["C"],
                "stock_C": st["C"],
                "elite_C": e["C"],
            }
        )

    n_fx = len(per_fx)
    success_gate = n_fx > 0 and n_ok >= min(6, max(1, int(0.75 * n_fx)))
    # Aggregate comparisons
    h_ok = adapt["avg_H"] >= elite["avg_H"] - 0.005
    c_recover = adapt["avg_C"] >= stock["avg_C"] - 0.03
    c_vs_elite = adapt["avg_C"] >= elite["avg_C"] - 0.005
    r_keep = adapt["avg_R"] >= elite["avg_R"] - 0.03

    if success_gate and h_ok and (c_recover or c_vs_elite):
        overall = "supported"
    elif h_ok and r_keep and (c_vs_elite or adapt["avg_C"] > elite["avg_C"]):
        overall = "mixed"
    elif adapt["avg_H"] >= stock["avg_H"] and adapt["avg_C"] > elite["avg_C"]:
        overall = "mixed"
    else:
        overall = "rejected"

    # Hybrid check
    hybrid_ok = (
        hybrid["avg_H"] >= elite["avg_H"] - 0.01
        and hybrid["avg_C"] >= elite["avg_C"] - 0.01
    )

    verdicts = [
        {
            "id": "RT4_adaptive_vs_elite_s2",
            "status": overall,
            "best_adaptive": best_adaptive_name,
            "fixture_ok": f"{n_ok}/{n_fx}",
            "adapt": {"C": adapt["avg_C"], "R": adapt["avg_R"], "H": adapt["avg_H"]},
            "elite": {"C": elite["avg_C"], "R": elite["avg_R"], "H": elite["avg_H"]},
            "stock": {"C": stock["avg_C"], "R": stock["avg_R"], "H": stock["avg_H"]},
            "h_ok": h_ok,
            "c_recover_vs_stock": c_recover,
            "c_vs_elite": c_vs_elite,
            "r_keep": r_keep,
        },
        {
            "id": "RT4_hybrid_interrupt",
            "status": "supported" if hybrid_ok else "rejected",
            "hybrid": {"C": hybrid["avg_C"], "R": hybrid["avg_R"], "H": hybrid["avg_H"]},
            "elite": {"C": elite["avg_C"], "R": elite["avg_R"], "H": elite["avg_H"]},
        },
        {
            "id": "RT4_elite_beats_stock_H",
            "status": "supported" if elite["avg_H"] >= stock["avg_H"] else "rejected",
            "elite_H": elite["avg_H"],
            "stock_H": stock["avg_H"],
            "elite_C": elite["avg_C"],
            "stock_C": stock["avg_C"],
        },
    ]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "experiment": "p0_rt4_adaptive_conflict",
        "theory_ids": ["RT4", "P7"],
        "stamp": stamp,
        "config": {
            "n_hops": n_hops,
            "seed": seed,
            "n_seeds": n_seeds,
            "n_fixtures": n_fixtures,
            "k": k,
            "elite_knobs": elite_knobs,
        },
        "summary_table": summary,
        "per_fixture": per_fx,
        "verdicts": verdicts,
        "overall_verdict": overall,
        "rows": rows,
    }
    jp = out_dir / f"rt4_adaptive_conflict_{stamp}.json"
    latest = out_dir / "rt4_adaptive_conflict_latest.json"
    text = json.dumps(payload, indent=2)
    jp.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")

    lines = [
        "# RT4 Adaptive Conflict Schedule",
        "",
        f"**Stamp:** {stamp} · overall=**{overall}** · best_adaptive=`{best_adaptive_name}`",
        "",
        "| condition | C | R | H | anchor_R | mono | thrash | trigger |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in summary:
        lines.append(
            f"| {s['condition']} | {s['avg_C']:.3f} | {s['avg_R']:.3f} | {s['avg_H']:.3f} | "
            f"{s['avg_anchor_R']:.3f} | {s['avg_layer_mono']:.3f} | {s['avg_thrash']:.3f} | "
            f"{s['trigger_rate']:.2f} |"
        )
    lines.append("")
    lines.append("## Verdicts")
    for v in verdicts:
        lines.append(
            f"- **{v['id']}**: `{v['status']}` — "
            f"`{json.dumps({k: v[k] for k in v if k not in ('id', 'status')}, default=str)}`"
        )
    lines.append("")
    lines.append("## Per-fixture adaptive vs elite")
    for pfx in per_fx:
        lines.append(
            f"- `{pfx['fixture']}`: ok={pfx['ok']} "
            f"H {pfx['adapt_H']:.3f} vs elite {pfx['elite_H']:.3f}; "
            f"C {pfx['adapt_C']:.3f} (stock {pfx['stock_C']:.3f})"
        )
    md_path = out_dir / f"rt4_adaptive_conflict_{stamp}.md"
    latest_md = out_dir / "rt4_adaptive_conflict_latest.md"
    md = "\n".join(lines) + "\n"
    md_path.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        chart_dir = out_dir / "charts"
        chart_dir.mkdir(parents=True, exist_ok=True)
        focus = [
            sm[c]
            for c in (
                "stock_v2_s3_mpH",
                "elite_fixed_s2_mpH",
                best_adaptive_name,
                "hybrid_interrupt",
            )
        ]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        xs = range(len(focus))
        ax.bar([i - 0.2 for i in xs], [s["avg_C"] for s in focus], width=0.2, label="C")
        ax.bar([i for i in xs], [s["avg_R"] for s in focus], width=0.2, label="R")
        ax.bar([i + 0.2 for i in xs], [s["avg_H"] for s in focus], width=0.2, label="H")
        ax.set_xticks(list(xs))
        ax.set_xticklabels([s["condition"].replace("_", "\n") for s in focus], fontsize=7)
        ax.set_ylim(0, 1.05)
        ax.legend()
        ax.set_title("RT4 adaptive vs elite schedule=2")
        fig.tight_layout()
        cpath = chart_dir / "rt4_adaptive_conflict.png"
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
    print("\n=== RT4 adaptive conflict ===")
    print(f"overall={payload['overall_verdict']}")
    for s in payload["summary_table"]:
        print(
            f"{s['condition']:24s}  C={s['avg_C']:.3f} R={s['avg_R']:.3f} H={s['avg_H']:.3f} "
            f"trig={s['trigger_rate']:.2f}"
        )
    for v in payload["verdicts"]:
        print(f"  {v['id']}: {v['status']}")
    print(f"\nWrote {payload['paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
