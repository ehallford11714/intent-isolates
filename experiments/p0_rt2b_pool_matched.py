#!/usr/bin/env python3
"""RT2b — pool-matched protect vs truncate (fair H comparison).

Forces identical pool_n / path_len budget after compact so truncate cannot win
H via larger pool. Pads truncate pool with cold filler spans or subsamples
protect filler to match.

Success: protect mid_R ≥ truncate+0.15 AND H ≥ truncate−0.01 under matched
coverage ±10% / matched pool_n.

Usage::

    python experiments/p0_rt2b_pool_matched.py
"""

from __future__ import annotations

import argparse
import json
import re
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

_RESEARCH = _ROOT.parent
_PD_SRC = _RESEARCH / "PromptDictCompress" / "src"
if _PD_SRC.is_dir() and str(_PD_SRC) not in sys.path:
    sys.path.insert(0, str(_PD_SRC))

from intentisolates import (  # noqa: E402
    CreativeBurstHopper,
    CreativityMeter,
    identify_span_isolates,
)
from intentisolates.span_burst import filter_spans_for_burst, multi_path_burst  # noqa: E402
from intentisolates.types import SpanIsolate, TextSpan  # noqa: E402

from theory_corpus_sweep import FIXTURES  # type: ignore  # noqa: E402

_HIGH_VALUE_RE = re.compile(
    r"(?i)\b(goal|constraint|must not|cannot|deadline|budget|require|"
    r"outcome|result|objective|aim to|i want|i need)\b"
)

_PROMPTDICT = False
try:
    from promptdict.compressor import DictCompressor  # noqa: E402
    from promptdict.metrics import estimate_tokens  # noqa: E402

    _PROMPTDICT = True
except ImportError:  # pragma: no cover
    DictCompressor = None  # type: ignore
    estimate_tokens = None  # type: ignore

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


def _tok_est(text: str) -> int:
    if estimate_tokens is not None:
        return int(estimate_tokens(text))
    return max(1, len(text.split()))


def _protect_compact(text: str, *, budget: int) -> tuple[str, dict[str, Any]]:
    before = _tok_est(text)
    sentences = re.split(r"(?<=[.!?\n])\s+", text)
    keep: list[str] = []
    rest: list[str] = []
    for s in sentences:
        if _HIGH_VALUE_RE.search(s):
            keep.append(s)
        else:
            rest.append(s)
    keep_blob = "\n".join(keep) if keep else text
    rest_blob = "\n".join(rest)
    meta: dict[str, Any] = {
        "backend": "promptdict" if _PROMPTDICT else "keyword_fallback",
        "n_keep": len(keep),
        "n_rest": len(rest),
        "budget": budget,
    }
    visible = keep_blob
    if DictCompressor is not None and rest_blob.strip():
        comp = DictCompressor(min_freq=2, max_dict_size=128)
        enc = comp.compress(rest_blob)
        if enc and enc.dictionary:
            visible = (
                keep_blob
                + "\n\n<<<COMPACTED_FILLER dict-encoded>>>\n"
                + enc.packed_prompt
            )
            if _tok_est(visible) > budget:
                visible = (
                    keep_blob
                    + f"\n\n[filler dict cold ~{enc.metrics.packed_tokens} tok omitted]"
                )
                meta["hot_trim"] = True
    else:
        words = rest_blob.split()
        room = max(0, budget - _tok_est(keep_blob) - 4)
        visible = keep_blob + ("\n" + " ".join(words[:room]) if room and words else "")
    meta["tokens_before"] = before
    meta["tokens_after"] = _tok_est(visible)
    return visible, meta


def _lossy_truncate(text: str, *, budget: int) -> tuple[str, dict[str, Any]]:
    before = _tok_est(text)
    words = text.split()
    if before <= budget or len(words) <= 8:
        return text, {
            "tokens_before": before,
            "tokens_after": before,
            "mode": "truncate_noop",
            "budget": budget,
        }
    keep = max(8, budget)
    head = keep // 2
    tail = keep - head
    out = " ".join(words[:head] + ["[...truncated...]"] + words[-tail:])
    after = _tok_est(out)
    if after > budget:
        target_chars = max(200, budget * 4)
        if len(out) > target_chars:
            h = target_chars // 2
            out = out[:h] + "\n[...truncated...]\n" + out[-h:]
            after = _tok_est(out)
    return out, {
        "tokens_before": before,
        "tokens_after": after,
        "mode": "lossy_truncate",
        "budget": budget,
    }


def _mid_constraint_retention(orig_spans: Sequence[Any], text_after: str) -> float:
    mid = [
        s
        for s in orig_spans
        if _typ(s.typology) in ("goal", "constraint")
    ]
    n = len(orig_spans)
    if n >= 6:
        lo, hi = n // 5, n - n // 5
        mid_pos = [
            s
            for i, s in enumerate(orig_spans)
            if lo <= i < hi and _typ(s.typology) in ("goal", "constraint")
        ]
        if mid_pos:
            mid = mid_pos
    if not mid:
        mid = [s for s in orig_spans if _typ(s.typology) == "constraint"]
    if not mid:
        return 1.0
    t = text_after.lower()
    hits = 0
    for s in mid:
        surf = (getattr(s, "surface", None) or getattr(s, "text", "") or "").strip().lower()
        if not surf:
            continue
        toks = [w for w in re.findall(r"[a-z0-9]+", surf) if len(w) >= 4]
        if not toks:
            continue
        if sum(1 for w in toks if w in t) / len(toks) >= 0.5:
            hits += 1
    return hits / max(1, len(mid))


def _clone_span(s: Any, new_id: str) -> Any:
    """Clone with a new id for cold-pad filler (non-protect)."""
    surf = str(getattr(s, "surface", None) or getattr(s, "text", "cold_pad") or "cold_pad")
    start = int(getattr(s, "start", 0))
    end = int(getattr(s, "end", start + max(1, len(surf))))
    return SpanIsolate(
        id=new_id,
        typology=getattr(s, "typology", "noise"),
        text_span=TextSpan(start=start, end=end, surface=surf),
        layer=getattr(s, "layer", 2),
        hop_weight=float(getattr(s, "hop_weight", 0.3)),
        burst_affinity=float(getattr(s, "burst_affinity", 0.2)),
        protect=False,
        source="cold_pad",
    )


def _match_pools(
    protect_spans: list[Any],
    truncate_spans: list[Any],
    cold_bank: Sequence[Any],
    *,
    seed: int,
) -> tuple[list[Any], list[Any], dict[str, Any]]:
    """Force identical pool_n: pad smaller with cold refs or subsample larger."""
    import random as _random

    rng = _random.Random(seed)
    p = list(protect_spans)
    t = list(truncate_spans)
    meta: dict[str, Any] = {"protect_raw": len(p), "truncate_raw": len(t)}

    target = min(len(p), len(t))
    if target < 3:
        target = max(len(p), len(t), 3)

    # Prefer matching to the smaller pool so we don't invent too many pads
    target = min(len(p), len(t)) if min(len(p), len(t)) >= 3 else max(len(p), len(t))

    def _subsample(pool: list[Any], n: int) -> list[Any]:
        if len(pool) <= n:
            return pool
        # Keep protect/goal/constraint first, then fill
        anchors = [s for s in pool if getattr(s, "protect", False) or _typ(s.typology) in ("goal", "constraint")]
        rest = [s for s in pool if s not in anchors]
        rng.shuffle(rest)
        out = anchors[:n]
        need = n - len(out)
        out.extend(rest[:need])
        if len(out) < n:
            # still short: take any remaining
            leftover = [s for s in pool if s not in out]
            out.extend(leftover[: n - len(out)])
        return out[:n]

    def _pad(pool: list[Any], n: int, tag: str) -> list[Any]:
        if len(pool) >= n:
            return _subsample(pool, n)
        out = list(pool)
        bank = list(cold_bank) or list(pool)
        i = 0
        while len(out) < n and bank:
            src = bank[i % len(bank)]
            out.append(_clone_span(src, f"cold_{tag}_{i}_{getattr(src, 'id', i)}"))
            i += 1
            if i > n * 4:
                break
        return out

    # Match both to same target = max(min sizes with pad of smaller to larger if close)
    # Spec: pad truncate with cold OR subsample protect filler → equal pool_n
    if len(p) == len(t):
        meta["match_mode"] = "already_equal"
        return p, t, meta

    if abs(len(p) - len(t)) <= 2:
        target = max(len(p), len(t))
        p2 = _pad(p, target, "p")
        t2 = _pad(t, target, "t")
        meta["match_mode"] = "pad_to_max"
    elif len(p) > len(t):
        # subsample protect filler down toward truncate, then pad truncate up if needed
        target = len(t)
        if target < 3:
            target = 3
            t2 = _pad(t, target, "t")
            p2 = _subsample(p, target)
        else:
            p2 = _subsample(p, target)
            t2 = list(t)
        meta["match_mode"] = "subsample_protect"
    else:
        target = len(p)
        if target < 3:
            target = 3
            p2 = _pad(p, target, "p")
            t2 = _subsample(t, target) if len(t) >= target else _pad(t, target, "t")
        else:
            p2 = list(p)
            t2 = _pad(t, target, "t")
        meta["match_mode"] = "pad_truncate"

    # Final hard equalize
    n = min(len(p2), len(t2))
    if n < 3:
        n = max(len(p2), len(t2), 3)
        p2 = _pad(p2, n, "p_final")
        t2 = _pad(t2, n, "t_final")
    else:
        p2 = p2[:n]
        t2 = t2[:n]
    meta["pool_n_matched"] = n
    meta["protect_final"] = len(p2)
    meta["truncate_final"] = len(t2)
    return p2, t2, meta


def _coverage(path: Any, pool: Sequence[Any]) -> float:
    if not pool or not path.span_ids:
        return 0.0
    return len(set(path.span_ids)) / max(1, len(pool))


def _ratio_ok(a: float, b: float, tol: float = 0.10) -> bool:
    if b <= 1e-9:
        return a <= 1e-9
    return abs(a / b - 1.0) <= tol


def run(
    *,
    n_hops: int = 5,
    seed: int = 17,
    n_seeds: int = 5,
    n_fixtures: int = 8,
    budget: int = 120,
    k: int = 7,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    out_dir = out_dir or (_ROOT / "experiments" / "results")
    out_dir.mkdir(parents=True, exist_ok=True)
    fixtures = FIXTURES[:n_fixtures]
    meter = CreativityMeter()
    rows: list[dict[str, Any]] = []
    by_cond: dict[str, list[dict[str, Any]]] = defaultdict(list)
    match_metas: list[dict[str, Any]] = []

    conditions = (
        "protect_mpH_matched",
        "truncate_mpH_matched",
        "protect_v2_matched",
        "truncate_v2_matched",
        "raw_mpH",
    )

    for fix in fixtures:
        orig = identify_span_isolates(fix["text"], backend="rule")
        if len(orig) < 3:
            continue
        prot_text, prot_meta = _protect_compact(fix["text"], budget=budget)
        match_budget = max(40, int(prot_meta["tokens_after"]))
        trunc_text, trunc_meta = _lossy_truncate(fix["text"], budget=match_budget)

        mid_prot = _mid_constraint_retention(orig, prot_text)
        mid_trunc = _mid_constraint_retention(orig, trunc_text)
        mid_raw = _mid_constraint_retention(orig, fix["text"])

        prot_spans = identify_span_isolates(prot_text, backend="rule")
        filt = filter_spans_for_burst(prot_spans, drop_noise=True)
        prot_spans = filt if len(filt) >= 3 else prot_spans

        trunc_spans = identify_span_isolates(trunc_text, backend="rule")
        filt_t = [s for s in trunc_spans if _typ(s.typology) not in ("noise", "confounder")]
        trunc_spans = filt_t if len(filt_t) >= 3 else trunc_spans

        raw_spans = identify_span_isolates(fix["text"], backend="rule")
        cold_bank = [s for s in orig if _typ(s.typology) in ("noise", "confounder", "lexical")] or list(orig)

        prot_m, trunc_m, match_meta = _match_pools(
            prot_spans, trunc_spans, cold_bank, seed=seed + hash(fix["id"]) % 997
        )
        match_meta["fixture"] = fix["id"]
        match_metas.append(match_meta)

        pools = {
            "protect_mpH_matched": (prot_m, mid_prot, True),
            "truncate_mpH_matched": (trunc_m, mid_trunc, True),
            "protect_v2_matched": (prot_m, mid_prot, False),
            "truncate_v2_matched": (trunc_m, mid_trunc, False),
            "raw_mpH": (raw_spans, mid_raw, True),
        }

        for cond in conditions:
            spans, mid_r, use_mp = pools[cond]
            if len(spans) < 2:
                continue
            for si in range(n_seeds):
                s = seed + si * 17
                if use_mp:
                    path, _ = multi_path_burst(
                        spans,
                        n_hops=n_hops,
                        mode="creative_burst_v2",
                        k=k,
                        seed=s,
                        select_by="tradeoff_harmonic",
                        hopper_kwargs=ELITE_KNOBS,
                    )
                    hopper = CreativeBurstHopper.for_v2(spans, seed=s, **ELITE_KNOBS)
                else:
                    hopper = CreativeBurstHopper.for_v2(spans, seed=s, **ELITE_KNOBS)
                    path = hopper.burst_path(
                        seed=si % max(1, len(hopper.ordered)),
                        n_hops=n_hops,
                        mode="creative_burst_v2",
                    )
                report = meter.score_burst(
                    path, spans, motif_neighbors=hopper._motif_neighbors
                )
                cov = _coverage(path, spans)
                rec = {
                    "fixture": fix["id"],
                    "condition": cond,
                    "seed_offset": si,
                    "pool_n": len(spans),
                    "path_len": len(path.span_ids),
                    "coverage": round(cov, 4),
                    "mid_constraint_R": round(mid_r, 4),
                    "C": round(report.creativity_score, 4),
                    "R": round(report.reasoning_trace_score, 4),
                    "H": round(report.tradeoff_harmonic, 4),
                    "anchor_R": round(report.anchor_visit_rate, 4),
                    "layer_mono": round(report.layer_monotonicity, 4),
                    "tokens_protect": int(prot_meta.get("tokens_after", 0)),
                    "tokens_truncate": int(trunc_meta.get("tokens_after", 0)),
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
                "avg_mid_constraint_R": _mean([r["mid_constraint_R"] for r in rs]),
                "avg_coverage": _mean([r["coverage"] for r in rs]),
                "avg_path_len": _mean([float(r["path_len"]) for r in rs]),
                "avg_pool_n": _mean([float(r["pool_n"]) for r in rs]),
            }
        )
    sm = {s["condition"]: s for s in summary}

    ap = sm["protect_mpH_matched"]
    cp = sm["truncate_mpH_matched"]
    pool_match = _ratio_ok(ap["avg_pool_n"], cp["avg_pool_n"], tol=0.05) or abs(
        ap["avg_pool_n"] - cp["avg_pool_n"]
    ) < 0.5
    path_match = _ratio_ok(ap["avg_path_len"], cp["avg_path_len"], tol=0.10)
    cov_match = _ratio_ok(ap["avg_coverage"], cp["avg_coverage"], tol=0.10)
    mid_win = ap["avg_mid_constraint_R"] >= cp["avg_mid_constraint_R"] + 0.15
    h_ok = ap["avg_H"] >= cp["avg_H"] - 0.01
    r_ok = ap["avg_R"] >= cp["avg_R"] - 0.01

    if mid_win and h_ok and pool_match and (path_match or cov_match):
        overall = "supported"
    elif mid_win and pool_match and (h_ok or r_ok):
        overall = "mixed"
    elif mid_win and not pool_match:
        overall = "mixed_pool_unmatched"
    else:
        overall = "rejected"

    verdicts = [
        {
            "id": "RT2b_pool_matched_protect_vs_truncate_mpH",
            "status": overall,
            "mid_R": {
                "protect": ap["avg_mid_constraint_R"],
                "truncate": cp["avg_mid_constraint_R"],
            },
            "R": {"protect": ap["avg_R"], "truncate": cp["avg_R"]},
            "H": {"protect": ap["avg_H"], "truncate": cp["avg_H"]},
            "pool_n": {"protect": ap["avg_pool_n"], "truncate": cp["avg_pool_n"]},
            "path_len": {"protect": ap["avg_path_len"], "truncate": cp["avg_path_len"]},
            "coverage": {"protect": ap["avg_coverage"], "truncate": cp["avg_coverage"]},
            "pool_matched": pool_match,
            "path_len_matched": path_match,
            "coverage_matched": cov_match,
            "mid_win": mid_win,
            "h_ok": h_ok,
        },
        {
            "id": "RT2b_protect_R_vs_raw",
            "status": (
                "supported"
                if ap["avg_R"] >= sm["raw_mpH"]["avg_R"] - 0.05
                else "rejected"
            ),
            "protect_R": ap["avg_R"],
            "raw_R": sm["raw_mpH"]["avg_R"],
        },
    ]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "experiment": "p0_rt2b_pool_matched",
        "theory_ids": ["RT2b", "RT2", "P6"],
        "stamp": stamp,
        "promptdict_available": _PROMPTDICT,
        "config": {
            "n_hops": n_hops,
            "seed": seed,
            "n_seeds": n_seeds,
            "n_fixtures": n_fixtures,
            "budget": budget,
            "k": k,
            "elite_knobs": ELITE_KNOBS,
        },
        "match_metas": match_metas,
        "summary_table": summary,
        "verdicts": verdicts,
        "overall_verdict": overall,
        "rows": rows,
    }

    jp = out_dir / f"rt2b_pool_matched_{stamp}.json"
    latest = out_dir / "rt2b_pool_matched_latest.json"
    text = json.dumps(payload, indent=2)
    jp.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")

    lines = [
        "# RT2b Pool-Matched Protect vs Truncate",
        "",
        f"**Stamp:** {stamp} · PromptDict={_PROMPTDICT} · overall=**{overall}**",
        "",
        f"Config: fixtures={n_fixtures} seeds={n_seeds} hops={n_hops} budget={budget} k={k}",
        "",
        "| condition | C | R | H | mid_R | coverage | path_len | pool |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in summary:
        lines.append(
            f"| {s['condition']} | {s['avg_C']:.3f} | {s['avg_R']:.3f} | {s['avg_H']:.3f} | "
            f"{s['avg_mid_constraint_R']:.3f} | {s['avg_coverage']:.3f} | {s['avg_path_len']:.2f} | "
            f"{s['avg_pool_n']:.1f} |"
        )
    lines.append("")
    lines.append("## Verdicts")
    for v in verdicts:
        lines.append(
            f"- **{v['id']}**: `{v['status']}` — "
            f"`{json.dumps({kk: v[kk] for kk in v if kk not in ('id', 'status')}, default=str)}`"
        )
    md_path = out_dir / f"rt2b_pool_matched_{stamp}.md"
    latest_md = out_dir / "rt2b_pool_matched_latest.md"
    md = "\n".join(lines) + "\n"
    md_path.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        chart_dir = out_dir / "charts"
        chart_dir.mkdir(parents=True, exist_ok=True)
        focus = [sm[c] for c in ("protect_mpH_matched", "truncate_mpH_matched", "raw_mpH")]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        xs = range(len(focus))
        ax.bar([i - 0.2 for i in xs], [s["avg_R"] for s in focus], width=0.2, label="R")
        ax.bar([i for i in xs], [s["avg_H"] for s in focus], width=0.2, label="H")
        ax.bar(
            [i + 0.2 for i in xs],
            [s["avg_mid_constraint_R"] for s in focus],
            width=0.2,
            label="mid_R",
        )
        ax.set_xticks(list(xs))
        ax.set_xticklabels([s["condition"].replace("_", "\n") for s in focus], fontsize=7)
        ax.set_ylim(0, 1.05)
        ax.legend()
        ax.set_title("RT2b pool-matched protect vs truncate")
        fig.tight_layout()
        cpath = chart_dir / "rt2b_pool_matched.png"
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
    p.add_argument("--budget", type=int, default=120)
    p.add_argument("--k", type=int, default=7)
    p.add_argument("--out-dir", type=Path, default=_ROOT / "experiments" / "results")
    args = p.parse_args(list(argv) if argv is not None else None)
    payload = run(
        n_hops=args.hops,
        seed=args.seed,
        n_seeds=args.seeds,
        n_fixtures=args.fixtures,
        budget=args.budget,
        k=args.k,
        out_dir=args.out_dir,
    )
    print("\n=== RT2b pool-matched protect vs truncate ===")
    print(f"overall={payload['overall_verdict']}  PromptDict={payload['promptdict_available']}")
    for s in payload["summary_table"]:
        print(
            f"{s['condition']:24s}  C={s['avg_C']:.3f} R={s['avg_R']:.3f} H={s['avg_H']:.3f} "
            f"mid_R={s['avg_mid_constraint_R']:.3f} pool={s['avg_pool_n']:.1f}"
        )
    for v in payload["verdicts"]:
        print(f"  {v['id']}: {v['status']}")
    print(f"\nWrote {payload['paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
