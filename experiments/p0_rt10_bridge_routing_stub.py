#!/usr/bin/env python3
"""RT10 — Bridge / Kineteq orchestration routing stub (dry-run).

After multipath winner, emit orchestration route:
  validate_iv / compact_protect / burst_again
with a rubric. No real Kineteq required.

Success: Gated rubric ≥ random + 0.2; illegal-route rate = 0
(IV when R low is illegal).

Usage::

    python experiments/p0_rt10_bridge_routing_stub.py
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
from intentisolates.orchestration import (  # noqa: E402
    KINETEQ_BACKEND_ABSENT,
    STAGE_BRIDGE_ROUTE,
    orchestration_meta,
)
from intentisolates.span_burst import filter_spans_for_burst, multi_path_burst  # noqa: E402

from theory_corpus_sweep import FIXTURES  # type: ignore  # noqa: E402

ELITE_KNOBS = {
    "anchor_schedule": 2,
    "anchor_pull": 0.80,
    "layer_bias": 0.47,
    "novelty_weight": 1.10,
    "motif_weight": 0.45,
    "side_hop_prob": 0.18,
}

ROUTES = ("validate_iv", "compact_protect", "burst_again")

# Rubric thresholds
R_IV_TAU = 0.78
H_BURST_TAU = 0.72
MID_PROTECT_TAU = 0.70


def _typ(v: Any) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _mean(xs: Sequence[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def _prepare_spans(text: str, protect: bool = True) -> list[Any]:
    spans = identify_span_isolates(text, backend="rule")
    if protect:
        filt = filter_spans_for_burst(spans, drop_noise=True)
        if len(filt) >= 3:
            return filt
    return spans


def _mid_proxy(spans: Sequence[Any], path_ids: Sequence[str]) -> float:
    """Proxy mid-constraint retention: fraction of mid goal/constraint spans visited."""
    n = len(spans)
    if n < 3:
        return 1.0
    lo, hi = n // 5, n - n // 5
    mid = [
        s
        for i, s in enumerate(spans)
        if lo <= i < hi and _typ(s.typology) in ("goal", "constraint")
    ]
    if not mid:
        mid = [s for s in spans if _typ(s.typology) in ("goal", "constraint")]
    if not mid:
        return 1.0
    visited = set(path_ids)
    return sum(1 for s in mid if s.id in visited) / len(mid)


def route_gated(meters: dict[str, float]) -> str:
    """Meter-gated orchestration route (production stub policy)."""
    r = meters["R"]
    h = meters["H"]
    mid = meters["mid_R"]
    c = meters["C"]
    # Illegal to validate_iv when R low — gated policy never does this
    if r >= R_IV_TAU and meters.get("layer_mono", 0) >= 0.55:
        return "validate_iv"
    if mid < MID_PROTECT_TAU or (r < 0.82 and mid < 0.85):
        return "compact_protect"
    if h < H_BURST_TAU or c > 0.78:
        return "burst_again"
    # Default: if high H/R already, validate; else burst
    if h >= H_BURST_TAU and r >= 0.75:
        return "validate_iv"
    return "burst_again"


def route_random(rng: random.Random) -> str:
    return rng.choice(ROUTES)


def route_select_by_c(meters: dict[str, float]) -> str:
    """Naive: high C → validate_iv (often illegal when R low)."""
    if meters["C"] >= 0.70:
        return "validate_iv"
    if meters["C"] >= 0.60:
        return "burst_again"
    return "compact_protect"


def rubric_score(route: str, meters: dict[str, float]) -> tuple[float, bool, str]:
    """Score route coherence; return (score∈[0,1], illegal, reason).

    Illegal: validate_iv when R < R_IV_TAU.
    """
    r, h, mid, c = meters["R"], meters["H"], meters["mid_R"], meters["C"]
    illegal = route == "validate_iv" and r < R_IV_TAU
    if illegal:
        return 0.0, True, "illegal_iv_low_R"

    score = 0.0
    reason_bits = []
    if route == "validate_iv":
        # Reward high R + mono readiness
        score = 0.55 + 0.25 * min(1.0, (r - R_IV_TAU) / 0.15) + 0.20 * min(
            1.0, meters.get("layer_mono", 0.5)
        )
        reason_bits.append("iv_ready")
    elif route == "compact_protect":
        # Reward when mid low or R soft
        need = max(0.0, MID_PROTECT_TAU - mid) + max(0.0, 0.82 - r) * 0.5
        score = 0.40 + 0.50 * min(1.0, need / 0.4) + 0.10 * (1.0 - c)
        reason_bits.append("protect_needed" if need > 0.05 else "protect_optional")
    else:  # burst_again
        need = max(0.0, H_BURST_TAU - h) + max(0.0, c - 0.65) * 0.3
        score = 0.35 + 0.45 * min(1.0, need / 0.35) + 0.20 * min(1.0, c)
        reason_bits.append("explore_more")

    # Coherence bonus: route matches gated oracle
    oracle = route_gated(meters)
    if route == oracle:
        score = min(1.0, score + 0.15)
        reason_bits.append("matches_oracle")
    return round(min(1.0, max(0.0, score)), 4), False, "+".join(reason_bits)


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
    rng = random.Random(seed)

    policies = ("gated", "random", "select_by_C")
    rows: list[dict[str, Any]] = []
    by_pol: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for fix in fixtures:
        spans = _prepare_spans(fix["text"], protect=True)
        if len(spans) < 3:
            continue
        for si in range(n_seeds):
            s = seed + si * 17
            # Winner path: multipath H (elite)
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
            report = meter.score_burst(
                path, spans, motif_neighbors=hopper._motif_neighbors
            )
            meters = {
                "C": report.creativity_score,
                "R": report.reasoning_trace_score,
                "H": report.tradeoff_harmonic,
                "anchor_R": report.anchor_visit_rate,
                "layer_mono": report.layer_monotonicity,
                "mid_R": _mid_proxy(spans, path.span_ids),
            }

            for pol in policies:
                if pol == "gated":
                    route = route_gated(meters)
                elif pol == "random":
                    route = route_random(rng)
                else:
                    route = route_select_by_c(meters)
                score, illegal, reason = rubric_score(route, meters)
                orch = orchestration_meta(
                    stage=STAGE_BRIDGE_ROUTE,
                    kineteq_backend=KINETEQ_BACKEND_ABSENT,
                    theory_ids=["RT10", "B5", "P12"],
                    select_by="tradeoff_harmonic",
                )
                rec = {
                    "fixture": fix["id"],
                    "policy": pol,
                    "seed_offset": si,
                    "route": route,
                    "rubric": score,
                    "illegal": illegal,
                    "reason": reason,
                    "C": round(meters["C"], 4),
                    "R": round(meters["R"], 4),
                    "H": round(meters["H"], 4),
                    "mid_R": round(meters["mid_R"], 4),
                    "layer_mono": round(meters["layer_mono"], 4),
                    "orchestration": orch,
                    "kineteq_backend": KINETEQ_BACKEND_ABSENT,
                }
                rows.append(rec)
                by_pol[pol].append(rec)

    summary = []
    for pol in policies:
        rs = by_pol.get(pol, [])
        route_counts = defaultdict(int)
        for r in rs:
            route_counts[r["route"]] += 1
        summary.append(
            {
                "policy": pol,
                "n": len(rs),
                "avg_rubric": _mean([r["rubric"] for r in rs]),
                "illegal_rate": _mean([1.0 if r["illegal"] else 0.0 for r in rs]),
                "route_counts": dict(route_counts),
                "avg_R": _mean([r["R"] for r in rs]),
                "avg_H": _mean([r["H"] for r in rs]),
            }
        )
    sm = {s["policy"]: s for s in summary}
    gated = sm["gated"]
    rand = sm["random"]
    by_c = sm["select_by_C"]

    rubric_win = gated["avg_rubric"] >= rand["avg_rubric"] + 0.2
    illegal_ok = gated["illegal_rate"] <= 1e-9
    if rubric_win and illegal_ok:
        overall = "supported"
    elif illegal_ok and gated["avg_rubric"] >= rand["avg_rubric"] + 0.05:
        overall = "mixed"
    else:
        overall = "rejected"

    verdicts = [
        {
            "id": "RT10_gated_vs_random",
            "status": overall,
            "gated_rubric": gated["avg_rubric"],
            "random_rubric": rand["avg_rubric"],
            "delta": round(gated["avg_rubric"] - rand["avg_rubric"], 4),
            "gated_illegal_rate": gated["illegal_rate"],
            "select_by_C_illegal_rate": by_c["illegal_rate"],
            "select_by_C_rubric": by_c["avg_rubric"],
        },
        {
            "id": "RT10_illegal_route_zero",
            "status": "supported" if illegal_ok else "rejected",
            "illegal_rate": gated["illegal_rate"],
        },
    ]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "experiment": "p0_rt10_bridge_routing_stub",
        "theory_ids": ["RT10", "B5", "P12"],
        "stamp": stamp,
        "kineteq_backend": KINETEQ_BACKEND_ABSENT,
        "config": {
            "n_hops": n_hops,
            "seed": seed,
            "n_seeds": n_seeds,
            "n_fixtures": n_fixtures,
            "k": k,
            "R_IV_TAU": R_IV_TAU,
            "H_BURST_TAU": H_BURST_TAU,
            "MID_PROTECT_TAU": MID_PROTECT_TAU,
            "elite_knobs": ELITE_KNOBS,
        },
        "summary_table": summary,
        "verdicts": verdicts,
        "overall_verdict": overall,
        "rows": rows,
    }
    jp = out_dir / f"rt10_bridge_routing_{stamp}.json"
    latest = out_dir / "rt10_bridge_routing_latest.json"
    text = json.dumps(payload, indent=2)
    jp.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")

    lines = [
        "# RT10 Bridge / Kineteq Routing Stub",
        "",
        f"**Stamp:** {stamp} · overall=**{overall}** · kineteq_backend=`absent`",
        "",
        "| policy | rubric | illegal_rate | routes |",
        "| --- | ---: | ---: | --- |",
    ]
    for s in summary:
        lines.append(
            f"| {s['policy']} | {s['avg_rubric']:.3f} | {s['illegal_rate']:.3f} | "
            f"`{json.dumps(s['route_counts'])}` |"
        )
    lines.append("")
    lines.append("## Verdicts")
    for v in verdicts:
        lines.append(
            f"- **{v['id']}**: `{v['status']}` — "
            f"`{json.dumps({kk: v[kk] for kk in v if kk not in ('id', 'status')}, default=str)}`"
        )
    lines.append("")
    lines.append("## Route semantics")
    lines.append("- `validate_iv` — only when R≥τ (illegal otherwise)")
    lines.append("- `compact_protect` — when mid-constraint retention soft")
    lines.append("- `burst_again` — when H low or C still exploratory")
    md_path = out_dir / f"rt10_bridge_routing_{stamp}.md"
    latest_md = out_dir / "rt10_bridge_routing_latest.md"
    md = "\n".join(lines) + "\n"
    md_path.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        chart_dir = out_dir / "charts"
        chart_dir.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(7, 4))
        labels = [s["policy"] for s in summary]
        ax.bar(labels, [s["avg_rubric"] for s in summary], color="#5c4a2e", label="rubric")
        ax.bar(
            labels,
            [s["illegal_rate"] for s in summary],
            bottom=0,
            alpha=0.35,
            color="#a33",
            label="illegal_rate",
        )
        ax.set_ylim(0, 1.05)
        ax.legend()
        ax.set_title("RT10 routing stub rubric")
        fig.tight_layout()
        cpath = chart_dir / "rt10_bridge_routing.png"
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
    print("\n=== RT10 bridge routing stub ===")
    print(f"overall={payload['overall_verdict']}  kineteq={payload['kineteq_backend']}")
    for s in payload["summary_table"]:
        print(
            f"{s['policy']:14s}  rubric={s['avg_rubric']:.3f}  "
            f"illegal={s['illegal_rate']:.3f}  routes={s['route_counts']}"
        )
    print(f"\nWrote {payload['paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
