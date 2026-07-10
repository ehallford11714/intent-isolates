#!/usr/bin/env python3
"""RT1 satellite: multipath value-function bakeoff (H / R / C / iv_diag) × k.

Offline, modest fixture×seed budget. Writes results JSON + markdown table
for the iterative trainer to fold into RT1 epoch guidance.

Usage::

    python experiments/p0_multipath_selector_bakeoff.py
    python experiments/p0_multipath_selector_bakeoff.py --fixtures 4 --seeds 3 --k 3,5
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

from intentisolates import CreativityMeter, CreativeBurstHopper, identify_span_isolates  # noqa: E402
from intentisolates.span_burst import (  # noqa: E402
    layer_path_monotonicity,
    multi_path_burst,
)

sys.path.insert(0, str(_ROOT / "experiments"))
from theory_corpus_sweep import FIXTURES  # type: ignore  # noqa: E402

SELECT_ALIAS = {
    "H": "tradeoff_harmonic",
    "R": "reasoning_trace_score",
    "C": "creativity_score",
    "iv_diag": "iv_diag",  # handled locally
}


def _typ(v: Any) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _mean(xs: Sequence[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def _early_layer_frac(path_ids: Sequence[str], spans: Sequence[Any]) -> float:
    by_id = {s.id: s for s in spans}
    layers: list[int] = []
    for i in path_ids:
        if i not in by_id:
            continue
        ly = by_id[i].layer
        if isinstance(ly, int):
            layers.append(ly)
        else:
            s = str(ly)
            layers.append(int(s[1:]) if s.upper().startswith("L") and s[1:].isdigit() else (int(s) if s.isdigit() else 2))
    if not layers:
        return 0.0
    return sum(1 for L in layers if L <= 1) / len(layers)


def _iv_diag_score(report: Any, path_ids: Sequence[str], spans: Sequence[Any]) -> float:
    """RT1: 0.5·anchor_R + 0.3·layer_mono + 0.2·early_layer_frac."""
    anchor = float(report.anchor_visit_rate)
    mono = float(report.layer_monotonicity)
    early = _early_layer_frac(path_ids, spans)
    return 0.5 * anchor + 0.3 * mono + 0.2 * early


def _multipath_custom(
    spans: list[Any],
    *,
    n_hops: int,
    k: int,
    seed: int,
    select_by: str,
    knobs: dict[str, Any],
) -> tuple[Any, dict[str, Any]]:
    """Run k paths; select by stock meter key or iv_diag."""
    meter = CreativityMeter()
    hopper = CreativeBurstHopper.for_v2(spans, seed=seed, **knobs)
    n_seeds = max(1, min(k, len(spans)))
    candidates: list[dict[str, Any]] = []
    for i in range(n_seeds):
        h = CreativeBurstHopper.for_v2(
            spans,
            motifs=hopper.motifs,
            seed=seed + i * 31,
            **knobs,
        )
        path = h.burst_path(seed=i % max(1, len(h.ordered)), n_hops=n_hops, mode="creative_burst_v2")
        report = meter.score_burst(path, spans, motif_neighbors=h._motif_neighbors)
        if select_by == "iv_diag":
            score = _iv_diag_score(report, path.span_ids, spans)
        else:
            key = SELECT_ALIAS.get(select_by, select_by)
            score_map = {
                "tradeoff_harmonic": report.tradeoff_harmonic,
                "tradeoff_product": report.tradeoff_product,
                "creativity_score": report.creativity_score,
                "reasoning_trace_score": report.reasoning_trace_score,
                "anchor_visit_rate": report.anchor_visit_rate,
            }
            if key not in score_map:
                raise ValueError(f"Unknown select_by={select_by!r}")
            score = float(score_map[key])
        candidates.append(
            {
                "path": path,
                "report": report,
                "select_score": score,
                "seed_index": i,
                "C": report.creativity_score,
                "R": report.reasoning_trace_score,
                "H": report.tradeoff_harmonic,
                "anchor_R": report.anchor_visit_rate,
                "layer_mono": report.layer_monotonicity,
            }
        )
    candidates.sort(key=lambda c: (-float(c["select_score"]), c["seed_index"]))
    best = candidates[0]
    return best["path"], {
        "C": best["C"],
        "R": best["R"],
        "H": best["H"],
        "anchor_R": best["anchor_R"],
        "layer_mono": best["layer_mono"],
        "select_score": best["select_score"],
        "candidate_Hs": [c["H"] for c in candidates],
    }


def run(
    *,
    n_hops: int = 5,
    seed: int = 17,
    n_seeds: int = 3,
    n_fixtures: int = 4,
    ks: Sequence[int] = (3, 5),
    select_bys: Sequence[str] = ("H", "R", "C", "iv_diag"),
    out_dir: Path | None = None,
) -> dict[str, Any]:
    out_dir = out_dir or (_ROOT / "experiments" / "results")
    out_dir.mkdir(parents=True, exist_ok=True)
    fixtures = FIXTURES[:n_fixtures]
    rows: list[dict[str, Any]] = []
    by_cond: dict[str, list[dict[str, float]]] = defaultdict(list)

    for fx in fixtures:
        spans = identify_span_isolates(fx["text"], backend="rule")
        if len(spans) < 3:
            continue
        for k in ks:
            for sb in select_bys:
                cond_id = f"mp_k{k}_{sb}"
                for si in range(n_seeds):
                    path, m = _multipath_custom(
                        spans,
                        n_hops=n_hops,
                        k=k,
                        seed=seed + si * 17,
                        select_by=sb,
                        knobs={},
                    )
                    rec = {
                        "fixture": fx["id"],
                        "condition": cond_id,
                        "k": k,
                        "select_by": sb,
                        "seed_offset": si,
                        **{kk: round(float(m[kk]), 4) for kk in ("C", "R", "H", "anchor_R", "layer_mono")},
                    }
                    rows.append(rec)
                    by_cond[cond_id].append(rec)

    summary = []
    for cond, rs in sorted(by_cond.items()):
        summary.append(
            {
                "condition": cond,
                "n": len(rs),
                "avg_C": _mean([r["C"] for r in rs]),
                "avg_R": _mean([r["R"] for r in rs]),
                "avg_H": _mean([r["H"] for r in rs]),
                "avg_anchor_R": _mean([r["anchor_R"] for r in rs]),
                "avg_layer_mono": _mean([r["layer_mono"] for r in rs]),
            }
        )
    summary.sort(key=lambda r: -r["avg_H"])

    # RT1 adjudication
    best_h = summary[0] if summary else None
    by_sb: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for s in summary:
        # conditions are mp_k{K}_{select_by}; select_by may contain underscores (iv_diag)
        cond = s["condition"]
        if "_iv_diag" in cond:
            sb = "iv_diag"
        elif cond.endswith("_H"):
            sb = "H"
        elif cond.endswith("_R"):
            sb = "R"
        elif cond.endswith("_C"):
            sb = "C"
        else:
            sb = cond.rsplit("_", 1)[-1]
        by_sb[sb].append(s)
    mean_by_sb = {
        sb: {
            "avg_H": _mean([x["avg_H"] for x in xs]),
            "avg_R": _mean([x["avg_R"] for x in xs]),
            "avg_C": _mean([x["avg_C"] for x in xs]),
        }
        for sb, xs in by_sb.items()
    }
    verdicts: list[str] = []
    if "C" in mean_by_sb and "H" in mean_by_sb:
        if mean_by_sb["C"]["avg_R"] < mean_by_sb["H"]["avg_R"]:
            verdicts.append(
                f"RT1/G1 replicate: select-by-C R={mean_by_sb['C']['avg_R']:.3f} "
                f"< H R={mean_by_sb['H']['avg_R']:.3f}"
            )
        else:
            verdicts.append("RT1/G1 NOT replicated: select-by-C R not worse than H")
    if "iv_diag" in mean_by_sb and "H" in mean_by_sb:
        h0 = mean_by_sb["H"]
        iv = mean_by_sb["iv_diag"]
        ok_h = iv["avg_H"] >= h0["avg_H"] - 0.01
        ok_r = iv["avg_R"] >= h0["avg_R"] - 1e-9
        if ok_h and ok_r:
            verdicts.append(
                f"RT1 success (a): iv_diag H={iv['avg_H']:.3f} R={iv['avg_R']:.3f} "
                f"competitive with H={h0['avg_H']:.3f} R={h0['avg_R']:.3f}"
            )
        else:
            verdicts.append(
                f"RT1 partial: iv_diag H={iv['avg_H']:.3f} R={iv['avg_R']:.3f} vs "
                f"H={h0['avg_H']:.3f} R={h0['avg_R']:.3f} — Pareto map only"
            )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "experiment": "p0_multipath_selector_bakeoff",
        "theory_ids": ["RT1", "P13", "G1"],
        "stamp": stamp,
        "config": {
            "n_hops": n_hops,
            "seed": seed,
            "n_seeds": n_seeds,
            "n_fixtures": n_fixtures,
            "ks": list(ks),
            "select_bys": list(select_bys),
        },
        "summary_table": summary,
        "mean_by_select_by": mean_by_sb,
        "best_by_H": best_h,
        "verdict": verdicts,
        "rows": rows,
    }
    json_path = out_dir / f"rt1_multipath_bakeoff_{stamp}.json"
    latest = out_dir / "rt1_multipath_bakeoff_latest.json"
    md_path = out_dir / f"rt1_multipath_bakeoff_{stamp}.md"
    latest_md = out_dir / "rt1_multipath_bakeoff_latest.md"
    text = json.dumps(payload, indent=2)
    json_path.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")

    lines = [
        "# RT1 Multipath Value-Function Bakeoff",
        "",
        f"**Stamp:** {stamp}",
        "",
        "| condition | C | R | H | anchor_R | layer_mono |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in summary:
        lines.append(
            f"| {s['condition']} | {s['avg_C']:.3f} | {s['avg_R']:.3f} | "
            f"{s['avg_H']:.3f} | {s['avg_anchor_R']:.3f} | {s['avg_layer_mono']:.3f} |"
        )
    lines.append("")
    lines.append("## Verdict")
    for v in verdicts:
        lines.append(f"- {v}")
    md = "\n".join(lines) + "\n"
    md_path.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")
    payload["paths"] = {"json": str(json_path), "markdown": str(md_path)}
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hops", type=int, default=5)
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--seeds", type=int, default=3)
    p.add_argument("--fixtures", type=int, default=4)
    p.add_argument("--k", type=str, default="3,5", help="comma-separated k values")
    p.add_argument("--out-dir", type=Path, default=_ROOT / "experiments" / "results")
    args = p.parse_args(list(argv) if argv is not None else None)
    ks = tuple(int(x.strip()) for x in args.k.split(",") if x.strip())
    payload = run(
        n_hops=args.hops,
        seed=args.seed,
        n_seeds=args.seeds,
        n_fixtures=args.fixtures,
        ks=ks,
        out_dir=args.out_dir,
    )
    print("\n=== RT1 multipath bakeoff ===")
    for s in payload["summary_table"]:
        print(
            f"{s['condition']:18s}  C={s['avg_C']:.3f}  R={s['avg_R']:.3f}  "
            f"H={s['avg_H']:.3f}"
        )
    for v in payload["verdict"]:
        print(" ", v)
    print(f"\nWrote {payload['paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
