#!/usr/bin/env python3
"""RT2 satellite: protect_compact → burst coupling (goal-neglect redo).

Simulates protect preference vs no-protect filter vs truncate-matched pool
before creative_burst_v2. Soft-imports PromptDict when present; otherwise
uses isolate protect flags + filter_spans_for_burst (offline analog).

Usage::

    python experiments/p0_protect_compact_burst.py
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

_RESEARCH = _ROOT.parent
for _sib in (_RESEARCH / "PromptDictCompress" / "src",):
    if _sib.is_dir() and str(_sib) not in sys.path:
        sys.path.insert(0, str(_sib))

from intentisolates import CreativityMeter, CreativeBurstHopper, identify_span_isolates  # noqa: E402
from intentisolates.span_burst import filter_spans_for_burst  # noqa: E402

sys.path.insert(0, str(_ROOT / "experiments"))
from theory_corpus_sweep import FIXTURES  # type: ignore  # noqa: E402

_HAS_PROMPDICT = False
try:
    from promptdict.compressor import DictCompressor  # noqa: F401

    _HAS_PROMPDICT = True
except ImportError:
    pass


def _typ(v: Any) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _mean(xs: Sequence[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def _mid_anchor_ids(spans: Sequence[Any]) -> set[str]:
    n = len(spans)
    lo, hi = max(1, n // 5), n - max(1, n // 5)
    out: set[str] = set()
    for i, s in enumerate(spans):
        if lo <= i < hi and (
            getattr(s, "protect", False) or _typ(s.typology) in ("goal", "constraint")
        ):
            out.add(s.id)
    return out


def _prepare_pools(spans: list[Any]) -> dict[str, tuple[list[Any], float, bool]]:
    """Return condition → (pool, mid_R proxy, goal_neglect_flag)."""
    mid_full = _mid_anchor_ids(spans)
    # A: protect preference
    a = filter_spans_for_burst(spans, drop_noise=True)
    if len(a) < 3:
        a = list(spans)
    mid_a = _mid_anchor_ids(a) & mid_full if mid_full else set()
    mid_r_a = (len(mid_a) / len(mid_full)) if mid_full else 1.0

    # B: filter without protect preference — hot = non-protect only, then allow all non-noise
    # Drop protect preference: treat protect like any span but still drop noise
    b = []
    for s in spans:
        typ = _typ(s.typology)
        if typ in ("noise", "confounder"):
            continue
        b.append(s)
    if len(b) < 3:
        b = list(spans)
    # Simulate "drop protect preference" by optionally demoting mid protect from scoring pool:
    # keep spans but mark goal_neglect if we exclude mid protect
    b_no_pref = [s for s in b if not (getattr(s, "protect", False) and s.id in mid_full)]
    if len(b_no_pref) >= 3:
        b_use = b_no_pref
        neglect_b = bool(mid_full) and not any(s.id in mid_full for s in b_use)
    else:
        b_use = b
        neglect_b = False
    mid_b = _mid_anchor_ids(b_use) & mid_full if mid_full else set()
    mid_r_b = (len(mid_b) / len(mid_full)) if mid_full else 1.0

    # C: truncate-matched size to A's len — head/tail keep, drop mid
    target = len(a)
    c: list[Any] = []
    n = len(spans)
    for i, s in enumerate(spans):
        if i < max(1, n // 5) or i >= n - max(1, n // 5):
            c.append(s)
        if len(c) >= target:
            break
    # fill if short
    for s in spans:
        if len(c) >= target:
            break
        if s not in c:
            c.append(s)
    mid_c = _mid_anchor_ids(c) & mid_full if mid_full else set()
    mid_r_c = (len(mid_c) / len(mid_full)) if mid_full else 0.0
    neglect_c = bool(mid_full) and len(mid_c) < len(mid_full)

    # D: full baseline
    d = list(spans)
    mid_r_d = 1.0

    return {
        "A_protect_filter": (a, mid_r_a, False),
        "B_no_protect_pref": (b_use, mid_r_b, neglect_b),
        "C_truncate_matched": (c, mid_r_c, neglect_c),
        "D_no_compact": (d, mid_r_d, False),
    }


def run(
    *,
    n_hops: int = 5,
    seed: int = 17,
    n_seeds: int = 3,
    n_fixtures: int = 4,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    out_dir = out_dir or (_ROOT / "experiments" / "results")
    out_dir.mkdir(parents=True, exist_ok=True)
    fixtures = FIXTURES[:n_fixtures]
    meter = CreativityMeter()
    by_cond: dict[str, list[dict[str, float]]] = defaultdict(list)
    rows: list[dict[str, Any]] = []

    for fx in fixtures:
        spans = identify_span_isolates(fx["text"], backend="rule")
        if len(spans) < 3:
            continue
        pools = _prepare_pools(spans)
        for cond, (pool, mid_r, neglect) in pools.items():
            for si in range(n_seeds):
                h = CreativeBurstHopper.for_v2(pool, seed=seed + si * 17)
                path = h.burst_path(seed=0, n_hops=n_hops, mode="creative_burst_v2")
                report = meter.score_burst(path, pool, motif_neighbors=h._motif_neighbors)
                # coverage / length match check vs D
                cov = len(path.span_ids) / max(1, len(pool))
                rec = {
                    "fixture": fx["id"],
                    "condition": cond,
                    "seed_offset": si,
                    "pool_n": len(pool),
                    "path_len": len(path.span_ids),
                    "coverage": round(cov, 4),
                    "mid_constraint_R": round(mid_r, 4),
                    "goal_neglect": neglect,
                    "C": round(report.creativity_score, 4),
                    "R": round(report.reasoning_trace_score, 4),
                    "H": round(report.tradeoff_harmonic, 4),
                    "anchor_R": round(report.anchor_visit_rate, 4),
                    "layer_mono": round(report.layer_monotonicity, 4),
                }
                rows.append(rec)
                by_cond[cond].append(rec)

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
                "avg_mid_constraint_R": _mean([r["mid_constraint_R"] for r in rs]),
                "neglect_rate": _mean([1.0 if r["goal_neglect"] else 0.0 for r in rs]),
                "avg_pool_n": _mean([float(r["pool_n"]) for r in rs]),
                "avg_path_len": _mean([float(r["path_len"]) for r in rs]),
            }
        )

    by_id = {s["condition"]: s for s in summary}
    a, b, c, d = (
        by_id.get("A_protect_filter"),
        by_id.get("B_no_protect_pref"),
        by_id.get("C_truncate_matched"),
        by_id.get("D_no_compact"),
    )
    verdicts: list[str] = []
    if a and b:
        d_anchor = a["avg_anchor_R"] - b["avg_anchor_R"]
        if d_anchor >= 0.10:
            verdicts.append(f"RT2 success: A anchor_R − B = {d_anchor:+.3f} ≥ 0.10")
        else:
            verdicts.append(f"RT2 partial: A anchor_R − B = {d_anchor:+.3f} < 0.10")
        if a["avg_mid_constraint_R"] >= 0.95:
            verdicts.append(f"RT2 mid_R A={a['avg_mid_constraint_R']:.3f} ≥ 0.95")
        else:
            verdicts.append(f"RT2 mid_R A={a['avg_mid_constraint_R']:.3f} < 0.95")
    if a and d:
        if a["avg_R"] >= d["avg_R"] - 0.05:
            verdicts.append(f"RT2 R gate: A R={a['avg_R']:.3f} ≥ D−0.05 ({d['avg_R']-0.05:.3f})")
        else:
            verdicts.append(f"RT2 R gate FAIL: A R={a['avg_R']:.3f} < D−0.05")
    if c and a:
        # fake-win check: C must not win solely via pool shrink
        path_ratio = c["avg_path_len"] / max(1e-6, a["avg_path_len"])
        if abs(path_ratio - 1.0) > 0.10 and c["avg_H"] > a["avg_H"]:
            verdicts.append(
                f"RT2 caution: C truncate may fake-win (path_len ratio={path_ratio:.2f})"
            )
        else:
            verdicts.append("RT2: truncate control does not clearly fake-win vs A")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "experiment": "p0_protect_compact_burst",
        "theory_ids": ["RT2", "P6"],
        "stamp": stamp,
        "promptdict_available": _HAS_PROMPDICT,
        "note": "Offline analog: filter_spans_for_burst + mid-anchor retention; soft PromptDict",
        "config": {"n_hops": n_hops, "seed": seed, "n_seeds": n_seeds, "n_fixtures": n_fixtures},
        "summary_table": summary,
        "verdict": verdicts,
        "rows": rows,
    }
    json_path = out_dir / f"rt2_protect_burst_{stamp}.json"
    latest = out_dir / "rt2_protect_burst_latest.json"
    md_path = out_dir / f"rt2_protect_burst_{stamp}.md"
    latest_md = out_dir / "rt2_protect_burst_latest.md"
    text = json.dumps(payload, indent=2)
    json_path.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    lines = [
        "# RT2 Protect-Compact → Burst",
        "",
        f"**Stamp:** {stamp} · PromptDict={_HAS_PROMPDICT}",
        "",
        "| condition | C | R | H | anchor_R | mid_R | neglect |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in summary:
        lines.append(
            f"| {s['condition']} | {s['avg_C']:.3f} | {s['avg_R']:.3f} | {s['avg_H']:.3f} | "
            f"{s['avg_anchor_R']:.3f} | {s['avg_mid_constraint_R']:.3f} | {s['neglect_rate']:.2f} |"
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
    p.add_argument("--out-dir", type=Path, default=_ROOT / "experiments" / "results")
    args = p.parse_args(list(argv) if argv is not None else None)
    payload = run(
        n_hops=args.hops,
        seed=args.seed,
        n_seeds=args.seeds,
        n_fixtures=args.fixtures,
        out_dir=args.out_dir,
    )
    print("\n=== RT2 protect->burst ===")
    for s in payload["summary_table"]:
        print(
            f"{s['condition']:22s}  C={s['avg_C']:.3f}  R={s['avg_R']:.3f}  "
            f"H={s['avg_H']:.3f}  mid_R={s['avg_mid_constraint_R']:.3f}"
        )
    for v in payload["verdict"]:
        print(" ", v)
    print(f"\nWrote {payload['paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
