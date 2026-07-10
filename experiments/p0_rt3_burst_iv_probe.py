#!/usr/bin/env python3
"""RT3 soft satellite: burst-proposed Z / IV-diagnostic structure (offline).

When LayerCausalSuite + mock_iv available, score early-layer instruments from
multipath-H vs multipath-C vs random paths. Soft-skips if causal deps missing.

Usage::

    python experiments/p0_rt3_burst_iv_probe.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from intentisolates import CreativityMeter, CreativeBurstHopper, identify_span_isolates  # noqa: E402
from intentisolates.span_burst import multi_path_burst  # noqa: E402

sys.path.insert(0, str(_ROOT / "experiments"))
from theory_corpus_sweep import FIXTURES  # type: ignore  # noqa: E402

_HAS_CAUSAL = False
try:
    from intentisolates.causal import LayerCausalSuite

    _HAS_CAUSAL = True
except ImportError:
    LayerCausalSuite = None  # type: ignore


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


def _z_candidates(path_ids: Sequence[str], spans: Sequence[Any]) -> list[str]:
    by_id = {s.id: s for s in spans}
    out = []
    for i in path_ids:
        if i not in by_id:
            continue
        s = by_id[i]
        if _layer_int(s.layer) <= 1 or _typ(s.typology) in ("tool", "instrument", "lexical"):
            out.append(i)
    return out


def run(*, n_hops: int = 5, seed: int = 17, out_dir: Path | None = None) -> dict[str, Any]:
    out_dir = out_dir or (_ROOT / "experiments" / "results")
    out_dir.mkdir(parents=True, exist_ok=True)
    # prefer causal fixtures
    fixtures = [f for f in FIXTURES if f.get("kind") == "causal"] or FIXTURES[:2]
    meter = CreativityMeter()
    rows: list[dict[str, Any]] = []
    iv_notes: list[str] = []

    for fx in fixtures:
        spans = identify_span_isolates(fx["text"], backend="rule")
        if len(spans) < 3:
            continue
        for select_by, label in (
            ("tradeoff_harmonic", "multipath_H"),
            ("creativity_score", "multipath_C"),
        ):
            path, _cands = multi_path_burst(
                spans, n_hops=n_hops, k=5, seed=seed, select_by=select_by, mode="creative_burst_v2"
            )
            report = meter.score_burst(path, spans)
            zs = _z_candidates(path.span_ids, spans)
            by_id = {s.id: s for s in spans}
            early = (
                sum(1 for i in path.span_ids if i in by_id and _layer_int(by_id[i].layer) <= 1)
                / max(1, len(path.span_ids))
                if path.span_ids
                else 0.0
            )
            rows.append(
                {
                    "fixture": fx["id"],
                    "condition": label,
                    "C": round(report.creativity_score, 4),
                    "R": round(report.reasoning_trace_score, 4),
                    "H": round(report.tradeoff_harmonic, 4),
                    "n_z_candidates": len(zs),
                    "z_ids": zs[:8],
                    "early_layer_frac": round(early, 4),
                }
            )
        # random path
        h = CreativeBurstHopper(spans, seed=seed + 99)
        rpath = h.burst_path(seed=0, n_hops=n_hops, mode="random")
        rrep = meter.score_burst(rpath, spans)
        zs = _z_candidates(rpath.span_ids, spans)
        rows.append(
            {
                "fixture": fx["id"],
                "condition": "random",
                "C": round(rrep.creativity_score, 4),
                "R": round(rrep.reasoning_trace_score, 4),
                "H": round(rrep.tradeoff_harmonic, 4),
                "n_z_candidates": len(zs),
                "z_ids": zs[:8],
            }
        )

        if _HAS_CAUSAL and LayerCausalSuite is not None:
            try:
                suite = LayerCausalSuite.from_text(fx["text"], backend="rule")
                result = suite.run(mock_iv=True)
                iv_notes.append(
                    {
                        "fixture": fx["id"],
                        "n_edges": len(getattr(result, "iv_edges", []) or []),
                        "notes": list(getattr(result, "notes", []) or [])[:5],
                        "mock_iv": True,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                iv_notes.append({"fixture": fx["id"], "error": str(exc)})

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    # aggregate Z counts
    from collections import defaultdict

    by_c: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_c[r["condition"]].append(r)

    def avg(key: str, rs: list[dict[str, Any]]) -> float:
        xs = [float(r.get(key, 0)) for r in rs]
        return round(sum(xs) / len(xs), 4) if xs else 0.0

    summary = [
        {
            "condition": c,
            "avg_H": avg("H", rs),
            "avg_R": avg("R", rs),
            "avg_n_z": avg("n_z_candidates", rs),
        }
        for c, rs in sorted(by_c.items())
    ]
    verdicts = [
        "RT3 structural probe: Z-candidate counts from paths (statistical F soft-skipped unless causaliv present).",
        f"causal_suite_available={_HAS_CAUSAL}",
    ]
    if summary:
        best_z = max(summary, key=lambda s: s["avg_n_z"])
        verdicts.append(f"Most Z candidates: {best_z['condition']} (avg_n_z={best_z['avg_n_z']:.2f})")

    payload = {
        "experiment": "p0_rt3_burst_iv_probe",
        "theory_ids": ["RT3", "B1"],
        "stamp": stamp,
        "has_causal": _HAS_CAUSAL,
        "summary_table": summary,
        "iv_notes": iv_notes,
        "verdict": verdicts,
        "rows": rows,
    }
    jp = out_dir / f"rt3_iv_probe_{stamp}.json"
    latest = out_dir / "rt3_iv_probe_latest.json"
    text = json.dumps(payload, indent=2)
    jp.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    md = out_dir / "rt3_iv_probe_latest.md"
    lines = ["# RT3 Burst-Proposed Z Probe", "", f"Stamp: {stamp}", ""]
    for s in summary:
        lines.append(f"- {s['condition']}: H={s['avg_H']:.3f} R={s['avg_R']:.3f} n_Z={s['avg_n_z']:.2f}")
    for v in verdicts:
        lines.append(f"- {v}")
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    payload["paths"] = {"json": str(jp), "markdown": str(md)}
    return payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hops", type=int, default=5)
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--out-dir", type=Path, default=_ROOT / "experiments" / "results")
    args = p.parse_args(list(argv) if argv is not None else None)
    payload = run(n_hops=args.hops, seed=args.seed, out_dir=args.out_dir)
    print("=== RT3 IV probe ===")
    for s in payload["summary_table"]:
        print(f"  {s['condition']}: H={s['avg_H']:.3f} n_Z={s['avg_n_z']:.2f}")
    for v in payload["verdict"]:
        print(" ", v)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
