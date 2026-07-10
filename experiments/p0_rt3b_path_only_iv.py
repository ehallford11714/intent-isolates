#!/usr/bin/env python3
"""RT3b — cleaner path-only IV (no Z-column boost / damp).

Builds feature frames from path-visited isolates as Z candidates only.
No damp/boost of columns. Reports first-stage F + weak rate via causaliv
when available; soft differentiable mock only as last resort.

Success: burst/high-R still beats random on ≥ majority fixtures, OR document
that boost was necessary (method note).

Usage::

    python experiments/p0_rt3b_path_only_iv.py
"""

from __future__ import annotations

import argparse
import json
import math
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
from intentisolates.span_burst import multi_path_burst  # noqa: E402

from theory_corpus_sweep import FIXTURES  # type: ignore  # noqa: E402

_HAS_SUITE = False
try:
    from intentisolates.causal import build_feature_frame, estimate_layer_iv
    from intentisolates.causal.features import MotifFeatureTable, pearson

    _HAS_SUITE = True
except ImportError:  # pragma: no cover
    build_feature_frame = None  # type: ignore
    estimate_layer_iv = None  # type: ignore
    MotifFeatureTable = None  # type: ignore
    pearson = None  # type: ignore

_HAS_CAUSALIV = False
_HAS_AUTOCAUSAL = False
try:
    import causaliv  # noqa: F401

    _HAS_CAUSALIV = True
except ImportError:
    pass
try:
    import autocausal  # noqa: F401

    _HAS_AUTOCAUSAL = True
except ImportError:
    pass

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


def _z_span_ids(path_ids: Sequence[str], spans: Sequence[Any]) -> list[str]:
    by_id = {s.id: s for s in spans}
    out = []
    for i in path_ids:
        s = by_id.get(i)
        if s is None:
            continue
        if _layer_int(s.layer) <= 1 or _typ(s.typology) in (
            "tool",
            "instrument",
            "lexical",
            "latent_feature",
        ):
            out.append(i)
    return out


def _column_for_span(span: Any) -> str:
    typ = _typ(span.typology)
    ly = _layer_int(span.layer)
    return f"isolate_{typ}_L{ly}".lower().replace("-", "_")


def _path_only_table(
    base: MotifFeatureTable,
    path_span_ids: Sequence[str],
    spans: Sequence[Any],
) -> MotifFeatureTable:
    """Restrict active Z candidates to columns implied by path-visited isolates.

    No boost/damp multipliers — only which early columns are eligible instruments.
    Non-path early columns are zeroed (hard mask), not softly dampened.
    """
    by = {s.id: s for s in spans}
    prefer_cols: list[str] = []
    seen: set[str] = set()
    for sid in path_span_ids:
        s = by.get(sid)
        if s is None:
            continue
        if _layer_int(s.layer) > 1 and _typ(s.typology) not in (
            "tool",
            "instrument",
            "lexical",
            "latent_feature",
        ):
            continue
        col = _column_for_span(s)
        if col in base.columns and col not in seen:
            seen.add(col)
            prefer_cols.append(col)
    y = base.outcome_column
    early = [
        c
        for c in base.columns
        if c != y and int(base.column_meta.get(c, {}).get("layer", 2)) <= 1
    ]
    if not prefer_cols:
        # Path had no early Z — use empty prefer → all early zeroed except first
        prefer_cols = early[:1] if early else []
    keep = set(prefer_cols[:3])
    rows = []
    for r in base.rows:
        nr = dict(r)
        for c in early:
            if c not in keep and c in nr:
                nr[c] = 0.0  # hard mask — no boost of keep set
        rows.append(nr)
    return MotifFeatureTable(
        rows=rows,
        columns=list(base.columns),
        outcome_column=base.outcome_column,
        column_meta=dict(base.column_meta),
        notes=list(base.notes) + [f"path_only_z={list(keep)}"],
    )


def _soft_path_mock_f(
    table: MotifFeatureTable,
    z_cols: Sequence[str],
    *,
    label: str,
) -> dict[str, Any]:
    """Soft F from |corr(Z,X)| only — no policy weight boost (cleaner than RT3)."""
    y = table.outcome_column
    cols = [c for c in table.columns if c != y]
    mid = [
        c for c in cols if int(table.column_meta.get(c, {}).get("layer", 2)) >= 2
    ] or cols[len(cols) // 3 :]
    if not z_cols:
        z_cols = cols[:1]
    f_vals = []
    for z in z_cols[:3]:
        if z not in table.columns:
            continue
        zs = [float(r[z]) for r in table.rows]
        # Skip all-zero Z (hard-masked)
        if sum(abs(v) for v in zs) < 1e-9:
            continue
        for x in mid[:3]:
            if x == z or x not in table.columns:
                continue
            xs = [float(r[x]) for r in table.rows]
            r = abs(pearson(zs, xs)) if pearson else 0.0
            f_vals.append(r * 40.0)
    mean_f = _mean(f_vals) if f_vals else 0.0
    return {
        "mean_first_stage_f": mean_f,
        "max_first_stage_f": round(max(f_vals), 4) if f_vals else 0.0,
        "n_edges": len(f_vals),
        "weak_rate": _mean([1.0 if f < 10 else 0.0 for f in f_vals]),
        "method": "soft_path_only_mock",
        "z_cols": list(z_cols)[:6],
        "label": label,
    }


def _score_iv_path_only(
    base: MotifFeatureTable,
    path_ids: Sequence[str],
    spans: Sequence[Any],
    *,
    label: str,
) -> dict[str, Any]:
    table = _path_only_table(base, path_ids, spans)
    z_cols = []
    by = {s.id: s for s in spans}
    for sid in path_ids:
        s = by.get(sid)
        if s is None:
            continue
        if _layer_int(s.layer) <= 1 or _typ(s.typology) in (
            "tool",
            "instrument",
            "lexical",
            "latent_feature",
        ):
            col = _column_for_span(s)
            if col in table.columns and col not in z_cols:
                z_cols.append(col)
    edges: list[Any] = []
    notes: list[str] = []
    method = "none"
    try:
        edges, notes = estimate_layer_iv(table, mock=False)
        if edges:
            method = edges[0].method
    except Exception as exc:  # noqa: BLE001
        notes.append(f"estimate_layer_iv error: {exc}")
    if not edges:
        soft = _soft_path_mock_f(table, z_cols, label=label)
        soft["notes"] = notes + ["fell_back_to_soft_path_mock"]
        return soft
    fs = [float(e.first_stage_f) for e in edges]
    weak = [
        1.0 if getattr(e, "weak_instrument", False) or e.first_stage_f < 10 else 0.0
        for e in edges
    ]
    edge_quality = [
        abs(float(e.beta_iv)) / (1.0 + (float(e.se) if e.se == e.se else 1.0))
        for e in edges
    ]
    return {
        "mean_first_stage_f": _mean(fs),
        "max_first_stage_f": round(max(fs), 4) if fs else 0.0,
        "n_edges": len(edges),
        "weak_rate": _mean(weak),
        "mean_edge_quality": _mean(edge_quality),
        "method": method,
        "z_cols": z_cols[:6],
        "notes": notes[:4],
        "label": label,
    }


def run(
    *,
    n_hops: int = 5,
    seed: int = 17,
    n_seeds: int = 3,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    out_dir = out_dir or (_ROOT / "experiments" / "results")
    out_dir.mkdir(parents=True, exist_ok=True)

    if not _HAS_SUITE:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        payload = {
            "experiment": "p0_rt3b_path_only_iv",
            "stamp": stamp,
            "soft_skip": True,
            "reason": "LayerCausalSuite / build_feature_frame unavailable",
            "overall_verdict": "soft_skip",
        }
        (out_dir / "rt3b_path_only_iv_latest.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        return payload

    fixtures = [f for f in FIXTURES if f.get("kind") == "causal"]
    extras = [
        f
        for f in FIXTURES
        if f["id"] in ("deploy_plan", "constraint_stack", "tool_log_repetitive")
    ]
    fixtures = fixtures + [e for e in extras if e not in fixtures]
    if not fixtures:
        fixtures = FIXTURES[:3]

    meter = CreativityMeter()
    rows: list[dict[str, Any]] = []
    fixture_wins: list[dict[str, Any]] = []

    for fix in fixtures:
        spans = identify_span_isolates(fix["text"], backend="rule")
        if len(spans) < 3:
            continue
        isolates = [s.to_isolate() for s in spans]
        base_table = build_feature_frame(isolates, n_bootstrap=48, seed=seed)

        # Aggregate path Z across seeds then score once per policy
        policy_paths: dict[str, list[list[str]]] = {
            "burst_multipath_H": [],
            "burst_high_R": [],
            "random_path": [],
            "convergent": [],
        }
        for si in range(n_seeds):
            s = seed + si * 17
            path_h, _ = multi_path_burst(
                spans,
                n_hops=n_hops,
                k=7,
                seed=s,
                select_by="tradeoff_harmonic",
                mode="creative_burst_v2",
                hopper_kwargs=ELITE_KNOBS,
            )
            path_r, _ = multi_path_burst(
                spans,
                n_hops=n_hops,
                k=5,
                seed=s,
                select_by="reasoning_trace_score",
                mode="creative_burst_v2",
                hopper_kwargs=ELITE_KNOBS,
            )
            path_rand = CreativeBurstHopper(spans, seed=s + 99).burst_path(
                seed=0, n_hops=n_hops, mode="random"
            )
            path_conv = CreativeBurstHopper.for_v2(
                spans, seed=s, novelty_weight=0.7, anchor_pull=0.95, side_hop_prob=0.05
            ).burst_path(seed=0, n_hops=n_hops, mode="creative_burst_v2")
            policy_paths["burst_multipath_H"].append(list(path_h.span_ids))
            policy_paths["burst_high_R"].append(list(path_r.span_ids))
            policy_paths["random_path"].append(list(path_rand.span_ids))
            policy_paths["convergent"].append(list(path_conv.span_ids))

        for label, path_list in policy_paths.items():
            # Union of Z candidates across seeds; score IV on union path ids
            union_ids: list[str] = []
            seen_ids: set[str] = set()
            meter_rows = []
            for path_ids in path_list:
                for sid in path_ids:
                    if sid not in seen_ids:
                        seen_ids.add(sid)
                        union_ids.append(sid)
                # re-score a representative path (last)
                fake_path_ids = path_ids
                # build a BurstPath-like score via hopper
            for si, path_ids in enumerate(path_list):
                s = seed + si * 17
                if label == "burst_multipath_H":
                    path, _ = multi_path_burst(
                        spans,
                        n_hops=n_hops,
                        k=7,
                        seed=s,
                        select_by="tradeoff_harmonic",
                        mode="creative_burst_v2",
                        hopper_kwargs=ELITE_KNOBS,
                    )
                elif label == "burst_high_R":
                    path, _ = multi_path_burst(
                        spans,
                        n_hops=n_hops,
                        k=5,
                        seed=s,
                        select_by="reasoning_trace_score",
                        mode="creative_burst_v2",
                        hopper_kwargs=ELITE_KNOBS,
                    )
                elif label == "random_path":
                    path = CreativeBurstHopper(spans, seed=s + 99).burst_path(
                        seed=0, n_hops=n_hops, mode="random"
                    )
                else:
                    path = CreativeBurstHopper.for_v2(
                        spans,
                        seed=s,
                        novelty_weight=0.7,
                        anchor_pull=0.95,
                        side_hop_prob=0.05,
                    ).burst_path(seed=0, n_hops=n_hops, mode="creative_burst_v2")
                meter_rows.append(meter.score_burst(path, spans))

            iv = _score_iv_path_only(base_table, union_ids, spans, label=label)
            n_z = len(_z_span_ids(union_ids, spans))
            rec = {
                "fixture": fix["id"],
                "condition": label,
                "n_z_cols": n_z,
                "z_cols": iv.get("z_cols", [])[:8],
                "mean_first_stage_f": iv["mean_first_stage_f"],
                "max_first_stage_f": iv["max_first_stage_f"],
                "weak_rate": iv["weak_rate"],
                "mean_edge_quality": iv.get("mean_edge_quality", 0.0),
                "iv_method": iv["method"],
                "avg_C": _mean([r.creativity_score for r in meter_rows]),
                "avg_R": _mean([r.reasoning_trace_score for r in meter_rows]),
                "avg_H": _mean([r.tradeoff_harmonic for r in meter_rows]),
                "boost_used": False,
            }
            rows.append(rec)

        fx_rows = [r for r in rows if r["fixture"] == fix["id"]]
        by_c = {r["condition"]: r for r in fx_rows}
        burst_best = max(
            (by_c[c] for c in ("burst_multipath_H", "burst_high_R") if c in by_c),
            key=lambda r: r["mean_first_stage_f"],
            default=None,
        )
        rand = by_c.get("random_path")
        if burst_best and rand:
            f_improve = burst_best["mean_first_stage_f"] >= rand["mean_first_stage_f"] * 1.10
            eq_improve = burst_best.get("mean_edge_quality", 0) >= rand.get(
                "mean_edge_quality", 0
            ) * 1.05 + 1e-9
            weak_improve = burst_best["weak_rate"] <= rand["weak_rate"] - 0.05
            win = f_improve or eq_improve or weak_improve
            fixture_wins.append(
                {
                    "fixture": fix["id"],
                    "burst_condition": burst_best["condition"],
                    "burst_F": burst_best["mean_first_stage_f"],
                    "random_F": rand["mean_first_stage_f"],
                    "rel_F": round(
                        burst_best["mean_first_stage_f"]
                        / max(1e-6, rand["mean_first_stage_f"]),
                        4,
                    ),
                    "win": win,
                    "reason": (
                        "F+10%"
                        if f_improve
                        else ("edge_q" if eq_improve else ("weak" if weak_improve else "none"))
                    ),
                }
            )

    by_cond: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(r)
    summary = []
    for cond, rs in sorted(by_cond.items()):
        summary.append(
            {
                "condition": cond,
                "n": len(rs),
                "avg_first_stage_f": _mean([r["mean_first_stage_f"] for r in rs]),
                "avg_max_f": _mean([r["max_first_stage_f"] for r in rs]),
                "avg_weak_rate": _mean([r["weak_rate"] for r in rs]),
                "avg_edge_quality": _mean([float(r.get("mean_edge_quality", 0)) for r in rs]),
                "avg_H": _mean([r["avg_H"] for r in rs]),
                "avg_R": _mean([r["avg_R"] for r in rs]),
                "avg_n_z": _mean([float(r["n_z_cols"]) for r in rs]),
                "methods": sorted({r["iv_method"] for r in rs}),
            }
        )

    n_fx = len(fixture_wins)
    n_win = sum(1 for w in fixture_wins if w["win"])
    majority = n_fx > 0 and n_win >= math.ceil(n_fx / 2)
    sm = {s["condition"]: s for s in summary}
    burst_f = max(
        (sm[c]["avg_first_stage_f"] for c in ("burst_multipath_H", "burst_high_R") if c in sm),
        default=0.0,
    )
    rand_f = sm.get("random_path", {}).get("avg_first_stage_f", 0.0)
    if majority and burst_f > rand_f:
        overall = "supported"
    elif majority or burst_f >= rand_f * 1.05:
        overall = "mixed"
    elif n_fx == 0:
        overall = "soft_skip"
    else:
        overall = "rejected"
        # Method note: boost may have been necessary in RT3
    method_note = (
        "path-only hard mask (no Z boost). "
        + (
            "Burst still wins majority; boost not required."
            if overall == "supported"
            else (
                "Burst does not clearly win without boost; RT3 boost may have been necessary."
                if overall == "rejected"
                else "Mixed without boost; treat RT3 F gains as partly identification-sensitive."
            )
        )
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "experiment": "p0_rt3b_path_only_iv",
        "theory_ids": ["RT3b", "RT3", "B1", "P11"],
        "stamp": stamp,
        "has_causaliv": _HAS_CAUSALIV,
        "has_autocausal": _HAS_AUTOCAUSAL,
        "has_suite": _HAS_SUITE,
        "boost_used": False,
        "method_note": method_note,
        "config": {"n_hops": n_hops, "seed": seed, "n_seeds": n_seeds},
        "summary_table": summary,
        "fixture_wins": fixture_wins,
        "n_fixture_wins": f"{n_win}/{n_fx}",
        "overall_verdict": overall,
        "rows": rows,
    }
    jp = out_dir / f"rt3b_path_only_iv_{stamp}.json"
    latest = out_dir / "rt3b_path_only_iv_latest.json"
    text = json.dumps(payload, indent=2)
    jp.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")

    lines = [
        "# RT3b Path-Only IV (No Z Boost)",
        "",
        f"**Stamp:** {stamp} · causaliv={_HAS_CAUSALIV} · autocausal={_HAS_AUTOCAUSAL}",
        f"**Overall:** **{overall}** · fixture wins `{n_win}/{n_fx}` · boost_used=False",
        "",
        f"**Method note:** {method_note}",
        "",
        "| condition | F | max_F | weak_rate | edge_q | H | R | n_Z | method |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for s in summary:
        lines.append(
            f"| {s['condition']} | {s['avg_first_stage_f']:.3f} | {s['avg_max_f']:.3f} | "
            f"{s['avg_weak_rate']:.3f} | {s['avg_edge_quality']:.3f} | {s['avg_H']:.3f} | "
            f"{s['avg_R']:.3f} | {s['avg_n_z']:.1f} | {','.join(s['methods'])} |"
        )
    lines.append("")
    lines.append("## Per-fixture wins (burst vs random)")
    for w in fixture_wins:
        lines.append(
            f"- `{w['fixture']}`: win={w['win']} ({w['reason']}) "
            f"F {w['burst_F']:.3f} vs {w['random_F']:.3f} (rel={w['rel_F']})"
        )
    md_path = out_dir / f"rt3b_path_only_iv_{stamp}.md"
    latest_md = out_dir / "rt3b_path_only_iv_latest.md"
    md = "\n".join(lines) + "\n"
    md_path.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        chart_dir = out_dir / "charts"
        chart_dir.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots(figsize=(8, 4))
        labels = [s["condition"] for s in summary]
        ax.bar(labels, [s["avg_first_stage_f"] for s in summary], color="#2f6f4e")
        ax.set_ylabel("mean first-stage F")
        ax.set_title("RT3b path-only IV (no Z boost)")
        ax.tick_params(axis="x", rotation=20, labelsize=8)
        fig.tight_layout()
        cpath = chart_dir / "rt3b_path_only_iv_f.png"
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
    p.add_argument("--seeds", type=int, default=3)
    p.add_argument("--out-dir", type=Path, default=_ROOT / "experiments" / "results")
    args = p.parse_args(list(argv) if argv is not None else None)
    payload = run(
        n_hops=args.hops, seed=args.seed, n_seeds=args.seeds, out_dir=args.out_dir
    )
    print("\n=== RT3b path-only IV ===")
    if payload.get("soft_skip"):
        print(" soft-skip:", payload.get("reason"))
        return 0
    print(f"overall={payload['overall_verdict']}  wins={payload['n_fixture_wins']}")
    print(f"causaliv={payload['has_causaliv']}  note={payload.get('method_note', '')[:80]}")
    for s in payload["summary_table"]:
        print(
            f"{s['condition']:22s}  F={s['avg_first_stage_f']:.3f}  "
            f"weak={s['avg_weak_rate']:.3f}  H={s['avg_H']:.3f}"
        )
    print(f"\nWrote {payload['paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
