#!/usr/bin/env python3
"""RT5 — longer-horizon mono-gating (hops ≥ 8).

Soft/hard mono-gate vs creative_burst_v2 / multipath_H at hops∈{8,10}.

Success: mono_gated or hard_plan mono ≥ layer_cot+0.05 and H ≥ elite_same_hops−0.02;
C ≥ motif_jump+0.08.

Usage::

    python experiments/p0_rt5_mono_gating.py
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
from intentisolates.span_burst import (  # noqa: E402
    filter_spans_for_burst,
    layer_path_monotonicity,
    multi_path_burst,
)
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


def _mean(xs: Sequence[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def _prepare_spans(text: str) -> list[Any]:
    spans = identify_span_isolates(text, backend="rule")
    filt = filter_spans_for_burst(spans, drop_noise=True)
    return filt if len(filt) >= 3 else spans


def _gated_path(
    spans: Sequence[Any],
    *,
    seed: int,
    n_hops: int,
    seed_index: int = 0,
    policy: str = "soft_mono",
    knobs: dict[str, Any] | None = None,
) -> BurstPath:
    """Build a continuous path with soft or hard mono constraints.

    soft_mono: reject hops with Δℓ < −1 more than once (allow one backstep).
    hard_plan: must visit ℓ≤1 before any ℓ≥3; prefer non-decreasing layers.
    """
    kw = dict(ELITE_KNOBS)
    if knobs:
        kw.update(knobs)
    if policy == "soft_mono":
        kw["layer_bias"] = min(1.2, float(kw.get("layer_bias", 0.47)) + 0.25)
    elif policy == "hard_plan":
        kw["layer_bias"] = min(1.2, float(kw.get("layer_bias", 0.47)) + 0.40)
        kw["side_hop_prob"] = min(0.08, float(kw.get("side_hop_prob", 0.18)))

    hopper = CreativeBurstHopper.for_v2(spans, seed=seed, **kw)
    hopper._v2_anchor_explicit = True
    start = hopper.ordered[seed_index % max(1, len(hopper.ordered))]
    rng = random.Random(seed + hash(start.id) % 10_000)
    visited: list[str] = [start.id]
    hops: list[Any] = []
    current = start
    backsteps = 0
    saw_early = _layer_int(start.layer) <= 1
    saw_late_before_early = False

    for _step in range(max(0, n_hops)):
        # Probe candidates via hopper scoring, then filter
        visited_set = set(visited)
        candidates = [s for s in hopper.spans if s.id not in visited_set]
        if not candidates:
            break

        scored: list[tuple[float, Any, str]] = []
        for cand in candidates:
            # Use hopper's internal next-hop score by temporarily asking
            # a one-step preference: reuse _next_hop but filter after
            pass

        # Get ranked preference by calling _next_hop repeatedly with exclusions
        excluded: set[str] = set()
        pick = None
        score = 0.0
        reason = ""
        for _attempt in range(min(12, len(candidates))):
            # Temporarily mark excluded as visited
            trial_visited = list(visited) + list(excluded)
            nxt, sc, rs = hopper._next_hop(
                current, trial_visited, mode="creative_burst_v2", rng=rng
            )
            if nxt is None:
                break
            cur_l = _layer_int(current.layer)
            nxt_l = _layer_int(nxt.layer)
            delta = nxt_l - cur_l
            reject = False
            if policy == "soft_mono":
                if delta < -1:
                    if backsteps >= 1:
                        reject = True
                    # else allow this one backstep
            elif policy == "hard_plan":
                if nxt_l >= 3 and not saw_early:
                    reject = True
                if delta < 0:
                    reject = True
            if reject:
                excluded.add(nxt.id)
                continue
            pick = nxt
            score = sc
            reason = rs
            if delta < -1:
                backsteps += 1
            break

        if pick is None:
            # Fallback: take best non-excluded even if soft-violating once
            nxt, sc, rs = hopper._next_hop(
                current, visited, mode="creative_burst_v2", rng=rng
            )
            if nxt is None:
                break
            pick, score, reason = nxt, sc, rs + ";gate_fallback"

        if _layer_int(pick.layer) <= 1:
            saw_early = True
        if _layer_int(pick.layer) >= 3 and not saw_early:
            saw_late_before_early = True

        hops.append(
            BurstHop(
                from_id=current.id,
                to_id=pick.id,
                mode="creative_burst_v2",
                score=round(score, 4),
                reason=reason + f";{policy}",
            )
        )
        visited.append(pick.id)
        current = pick

    typ_path = [_typ(hopper.by_id[i].typology) for i in visited if i in hopper.by_id]
    plan_ok = saw_early and not saw_late_before_early
    return BurstPath(
        seed_id=start.id,
        hops=hops,
        span_ids=visited,
        typology_path=typ_path,
        mode="creative_burst_v2",
        summary=f"mono_gate_{policy}",
        metadata={
            "policy": policy,
            "backsteps": backsteps,
            "plan_ok": plan_ok,
            "saw_early": saw_early,
        },
    )


def _multipath_gated(
    spans: Sequence[Any],
    *,
    seed: int,
    n_hops: int,
    k: int,
    policy: str,
    meter: CreativityMeter,
) -> BurstPath:
    best: BurstPath | None = None
    best_h = -1.0
    n_cand = max(1, min(k, len(spans)))
    for i in range(n_cand):
        path = _gated_path(
            spans, seed=seed + i * 31, n_hops=n_hops, seed_index=i, policy=policy
        )
        hopper = CreativeBurstHopper.for_v2(spans, seed=seed + i * 31, **ELITE_KNOBS)
        report = meter.score_burst(path, spans, motif_neighbors=hopper._motif_neighbors)
        if report.tradeoff_harmonic > best_h:
            best_h = report.tradeoff_harmonic
            best = path
    assert best is not None
    return best


def run(
    *,
    hop_budgets: Sequence[int] = (8, 10),
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

    conditions = (
        "elite_mpH",
        "v2_single",
        "layer_cot",
        "divergent",
        "motif_jump",
        "soft_mono_mpH",
        "hard_plan_mpH",
    )

    rows: list[dict[str, Any]] = []
    by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for n_hops in hop_budgets:
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
                    elif cond == "v2_single":
                        hopper = CreativeBurstHopper.for_v2(spans, seed=s, **ELITE_KNOBS)
                        path = hopper.burst_path(
                            seed=si % max(1, len(hopper.ordered)),
                            n_hops=n_hops,
                            mode="creative_burst_v2",
                        )
                    elif cond == "layer_cot":
                        hopper = CreativeBurstHopper.for_v2(
                            spans,
                            seed=s,
                            layer_bias=0.95,
                            novelty_weight=0.9,
                            side_hop_prob=0.08,
                            anchor_schedule=2,
                            anchor_pull=0.80,
                        )
                        path = hopper.burst_path(
                            seed=si % max(1, len(hopper.ordered)),
                            n_hops=n_hops,
                            mode="creative_burst_v2",
                        )
                    elif cond == "divergent":
                        hopper = CreativeBurstHopper.for_v2(
                            spans,
                            seed=s,
                            novelty_weight=1.4,
                            motif_weight=0.2,
                            side_hop_prob=0.28,
                            anchor_pull=0.45,
                            anchor_schedule=4,
                        )
                        path = hopper.burst_path(
                            seed=si % max(1, len(hopper.ordered)),
                            n_hops=n_hops,
                            mode="creative_burst_v2",
                        )
                    elif cond == "motif_jump":
                        hopper = CreativeBurstHopper(spans, seed=s)
                        path = hopper.burst_path(
                            seed=si % max(1, len(hopper.ordered)),
                            n_hops=n_hops,
                            mode="motif_jump",
                        )
                    elif cond == "soft_mono_mpH":
                        path = _multipath_gated(
                            spans,
                            seed=s,
                            n_hops=n_hops,
                            k=k,
                            policy="soft_mono",
                            meter=meter,
                        )
                        hopper = CreativeBurstHopper.for_v2(spans, seed=s, **ELITE_KNOBS)
                    else:  # hard_plan_mpH
                        path = _multipath_gated(
                            spans,
                            seed=s,
                            n_hops=n_hops,
                            k=k,
                            policy="hard_plan",
                            meter=meter,
                        )
                        hopper = CreativeBurstHopper.for_v2(spans, seed=s, **ELITE_KNOBS)

                    report = meter.score_burst(
                        path, spans, motif_neighbors=hopper._motif_neighbors
                    )
                    mono = layer_path_monotonicity(spans, path.span_ids)
                    plan_ok = bool(path.metadata.get("plan_ok", True))
                    rec = {
                        "fixture": fix["id"],
                        "n_hops": n_hops,
                        "condition": cond,
                        "seed_offset": si,
                        "C": round(report.creativity_score, 4),
                        "R": round(report.reasoning_trace_score, 4),
                        "H": round(report.tradeoff_harmonic, 4),
                        "anchor_R": round(report.anchor_visit_rate, 4),
                        "layer_mono": round(mono, 4),
                        "path_len": len(path.span_ids),
                        "plan_ok": plan_ok,
                    }
                    rows.append(rec)
                    by_key[f"{n_hops}:{cond}"].append(rec)

    summary = []
    for n_hops in hop_budgets:
        for cond in conditions:
            rs = by_key.get(f"{n_hops}:{cond}", [])
            summary.append(
                {
                    "n_hops": n_hops,
                    "condition": cond,
                    "n": len(rs),
                    "avg_C": _mean([r["C"] for r in rs]),
                    "avg_R": _mean([r["R"] for r in rs]),
                    "avg_H": _mean([r["H"] for r in rs]),
                    "avg_anchor_R": _mean([r["anchor_R"] for r in rs]),
                    "avg_layer_mono": _mean([r["layer_mono"] for r in rs]),
                    "plan_ok_rate": _mean([1.0 if r["plan_ok"] else 0.0 for r in rs]),
                }
            )
    sm = {(s["n_hops"], s["condition"]): s for s in summary}

    verdicts = []
    overall_flags = []
    for n_hops in hop_budgets:
        elite = sm[(n_hops, "elite_mpH")]
        layer = sm[(n_hops, "layer_cot")]
        motif = sm[(n_hops, "motif_jump")]
        soft = sm[(n_hops, "soft_mono_mpH")]
        hard = sm[(n_hops, "hard_plan_mpH")]

        def _ok(cand: dict[str, Any]) -> bool:
            return (
                cand["avg_layer_mono"] >= layer["avg_layer_mono"] + 0.05
                and cand["avg_H"] >= elite["avg_H"] - 0.02
                and cand["avg_C"] >= motif["avg_C"] + 0.08
            )

        soft_ok = _ok(soft)
        hard_ok = _ok(hard)
        status = (
            "supported"
            if soft_ok or hard_ok
            else (
                "mixed"
                if (
                    soft["avg_layer_mono"] >= layer["avg_layer_mono"]
                    or hard["avg_layer_mono"] >= layer["avg_layer_mono"]
                )
                and (soft["avg_H"] >= elite["avg_H"] - 0.04 or hard["avg_H"] >= elite["avg_H"] - 0.04)
                else "rejected"
            )
        )
        overall_flags.append(status)
        verdicts.append(
            {
                "id": f"RT5_mono_gate_hops{n_hops}",
                "status": status,
                "soft_ok": soft_ok,
                "hard_ok": hard_ok,
                "soft": {
                    "mono": soft["avg_layer_mono"],
                    "H": soft["avg_H"],
                    "C": soft["avg_C"],
                },
                "hard": {
                    "mono": hard["avg_layer_mono"],
                    "H": hard["avg_H"],
                    "C": hard["avg_C"],
                },
                "layer_cot_mono": layer["avg_layer_mono"],
                "elite_H": elite["avg_H"],
                "motif_C": motif["avg_C"],
            }
        )

    if all(f == "supported" for f in overall_flags):
        overall = "supported"
    elif any(f == "supported" for f in overall_flags) or any(f == "mixed" for f in overall_flags):
        overall = "mixed"
    else:
        overall = "rejected"

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "experiment": "p0_rt5_mono_gating",
        "theory_ids": ["RT5", "P3", "P14"],
        "stamp": stamp,
        "config": {
            "hop_budgets": list(hop_budgets),
            "seed": seed,
            "n_seeds": n_seeds,
            "n_fixtures": n_fixtures,
            "k": k,
            "elite_knobs": ELITE_KNOBS,
        },
        "summary_table": summary,
        "verdicts": verdicts,
        "overall_verdict": overall,
        "rows": rows,
    }
    jp = out_dir / f"rt5_mono_gating_{stamp}.json"
    latest = out_dir / "rt5_mono_gating_latest.json"
    text = json.dumps(payload, indent=2)
    jp.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")

    lines = [
        "# RT5 Longer-Horizon Mono-Gating",
        "",
        f"**Stamp:** {stamp} · overall=**{overall}** · hops={list(hop_budgets)}",
        "",
        "| hops | condition | C | R | H | mono | plan_ok |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in summary:
        lines.append(
            f"| {s['n_hops']} | {s['condition']} | {s['avg_C']:.3f} | {s['avg_R']:.3f} | "
            f"{s['avg_H']:.3f} | {s['avg_layer_mono']:.3f} | {s['plan_ok_rate']:.2f} |"
        )
    lines.append("")
    lines.append("## Verdicts")
    for v in verdicts:
        lines.append(
            f"- **{v['id']}**: `{v['status']}` — "
            f"`{json.dumps({kk: v[kk] for kk in v if kk not in ('id', 'status')}, default=str)}`"
        )
    md_path = out_dir / f"rt5_mono_gating_{stamp}.md"
    latest_md = out_dir / "rt5_mono_gating_latest.md"
    md = "\n".join(lines) + "\n"
    md_path.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        chart_dir = out_dir / "charts"
        chart_dir.mkdir(parents=True, exist_ok=True)
        for n_hops in hop_budgets:
            focus_conds = [
                "elite_mpH",
                "layer_cot",
                "soft_mono_mpH",
                "hard_plan_mpH",
                "motif_jump",
            ]
            focus = [sm[(n_hops, c)] for c in focus_conds]
            fig, ax = plt.subplots(figsize=(9, 4.5))
            xs = range(len(focus))
            ax.bar([i - 0.2 for i in xs], [s["avg_H"] for s in focus], width=0.2, label="H")
            ax.bar([i for i in xs], [s["avg_layer_mono"] for s in focus], width=0.2, label="mono")
            ax.bar([i + 0.2 for i in xs], [s["avg_C"] for s in focus], width=0.2, label="C")
            ax.set_xticks(list(xs))
            ax.set_xticklabels([s["condition"].replace("_", "\n") for s in focus], fontsize=7)
            ax.set_ylim(0, 1.05)
            ax.legend()
            ax.set_title(f"RT5 mono-gating hops={n_hops}")
            fig.tight_layout()
            cpath = chart_dir / f"rt5_mono_gating_h{n_hops}.png"
            fig.savefig(cpath, dpi=120)
            plt.close(fig)
        payload["chart"] = str(chart_dir / "rt5_mono_gating_h8.png")
    except Exception:
        pass

    payload["paths"] = {"json": str(jp), "markdown": str(md_path)}
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hops", type=int, nargs="+", default=[8, 10])
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--fixtures", type=int, default=8)
    p.add_argument("--k", type=int, default=7)
    p.add_argument("--out-dir", type=Path, default=_ROOT / "experiments" / "results")
    args = p.parse_args(list(argv) if argv is not None else None)
    payload = run(
        hop_budgets=args.hops,
        seed=args.seed,
        n_seeds=args.seeds,
        n_fixtures=args.fixtures,
        k=args.k,
        out_dir=args.out_dir,
    )
    print("\n=== RT5 longer-horizon mono-gating ===")
    print(f"overall={payload['overall_verdict']}")
    for s in payload["summary_table"]:
        if s["condition"] in ("elite_mpH", "soft_mono_mpH", "hard_plan_mpH", "layer_cot"):
            print(
                f"h{s['n_hops']} {s['condition']:16s}  "
                f"C={s['avg_C']:.3f} H={s['avg_H']:.3f} mono={s['avg_layer_mono']:.3f}"
            )
    for v in payload["verdicts"]:
        print(f"  {v['id']}: {v['status']}")
    print(f"\nWrote {payload['paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
