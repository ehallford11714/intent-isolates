#!/usr/bin/env python3
"""RT2 redesign: coverage-gated protect_compact → burst vs truncate → burst.

Uses real PromptDict protect_compact / lossy_truncate when available, matches
token budgets, then bursts with matched path-length / coverage gates.

Success: protect beats truncate on mid_constraint_R and R/H without collapsing
coverage (path_len / pool coverage within ±10% of partner when asserted).

Usage::

    python experiments/p0_rt2_protect_coverage_gated.py
    python experiments/p0_rt2_protect_coverage_gated.py --seeds 5 --fixtures 8
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
        # Fallback: keep protected + short head of filler under budget
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
    # Keep head/tail words approximating budget (middle dropped)
    keep = max(8, budget)
    head = keep // 2
    tail = keep - head
    out = " ".join(words[:head] + ["[...truncated...]"] + words[-tail:])
    after = _tok_est(out)
    # Char trim if still over
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
        and (getattr(s, "protect", False) or True)
    ]
    # Prefer mid-document anchors (positions in middle third)
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


def _coverage(path: Any, pool: Sequence[Any]) -> float:
    if not pool or not path.span_ids:
        return 0.0
    return len(set(path.span_ids)) / max(1, len(pool))


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

    conditions = (
        "A_protect_v2",
        "A_protect_mpH",
        "C_truncate_v2",
        "C_truncate_mpH",
        "D_raw_v2",
        "D_raw_mpH",
    )

    for fix in fixtures:
        orig = identify_span_isolates(fix["text"], backend="rule")
        if len(orig) < 3:
            continue
        # Match truncate budget to protect realized tokens (fair mid-drop control)
        prot_text, prot_meta = _protect_compact(fix["text"], budget=budget)
        match_budget = max(40, int(prot_meta["tokens_after"]))
        trunc_text, trunc_meta = _lossy_truncate(fix["text"], budget=match_budget)

        texts = {
            "A_protect_v2": (prot_text, prot_meta, True),
            "A_protect_mpH": (prot_text, prot_meta, True),
            "C_truncate_v2": (trunc_text, trunc_meta, False),
            "C_truncate_mpH": (trunc_text, trunc_meta, False),
            "D_raw_v2": (fix["text"], {"tokens_after": _tok_est(fix["text"])}, False),
            "D_raw_mpH": (fix["text"], {"tokens_after": _tok_est(fix["text"])}, False),
        }

        for cond in conditions:
            text, meta, use_protect_filter = texts[cond]
            mid_r = _mid_constraint_retention(orig, text)
            spans = identify_span_isolates(text, backend="rule")
            if use_protect_filter:
                filt = filter_spans_for_burst(spans, drop_noise=True)
                spans = filt if len(filt) >= 3 else spans
            elif cond.startswith("C_"):
                # truncate: drop noise only (no protect preference)
                filt = [s for s in spans if _typ(s.typology) not in ("noise", "confounder")]
                spans = filt if len(filt) >= 3 else spans
            if len(spans) < 2:
                spans = list(orig)

            use_mp = cond.endswith("mpH")
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
                    )
                    hopper = CreativeBurstHopper.for_v2(
                        spans, seed=s, anchor_schedule=2, anchor_pull=0.80
                    )
                else:
                    hopper = CreativeBurstHopper.for_v2(
                        spans, seed=s, anchor_schedule=2, anchor_pull=0.80
                    )
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
                    "tokens_after": int(meta.get("tokens_after", 0)),
                    "C": round(report.creativity_score, 4),
                    "R": round(report.reasoning_trace_score, 4),
                    "H": round(report.tradeoff_harmonic, 4),
                    "anchor_R": round(report.anchor_visit_rate, 4),
                    "layer_mono": round(report.layer_monotonicity, 4),
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
                "avg_tokens_after": _mean([float(r["tokens_after"]) for r in rs]),
            }
        )
    sm = {s["condition"]: s for s in summary}

    def _ratio_ok(a: float, b: float, tol: float = 0.10) -> bool:
        if b <= 1e-9:
            return a <= 1e-9
        return abs(a / b - 1.0) <= tol

    verdicts: list[dict[str, Any]] = []
    # Primary: protect_mpH vs truncate_mpH (coverage-gated)
    ap, cp = sm["A_protect_mpH"], sm["C_truncate_mpH"]
    cov_match = _ratio_ok(ap["avg_path_len"], cp["avg_path_len"]) and _ratio_ok(
        ap["avg_coverage"], cp["avg_coverage"], tol=0.15
    )
    mid_win = ap["avg_mid_constraint_R"] >= cp["avg_mid_constraint_R"] + 0.15
    rh_win = ap["avg_R"] >= cp["avg_R"] and ap["avg_H"] >= cp["avg_H"] - 0.01
    # Accept R/H win only if coverage not collapsed for protect relative to raw
    raw = sm["D_raw_mpH"]
    cov_alive = ap["avg_coverage"] >= raw["avg_coverage"] * 0.70 or ap["avg_pool_n"] >= 3
    if mid_win and (rh_win or ap["avg_R"] >= cp["avg_R"]) and cov_alive:
        status = "supported" if rh_win else "mixed_strong_mid"
    elif mid_win and not cov_alive:
        status = "mixed_coverage_collapse"
    elif mid_win:
        status = "mixed"
    else:
        status = "rejected"
    verdicts.append(
        {
            "id": "RT2_protect_vs_truncate_mpH",
            "status": status,
            "mid_R": {"protect": ap["avg_mid_constraint_R"], "truncate": cp["avg_mid_constraint_R"]},
            "R": {"protect": ap["avg_R"], "truncate": cp["avg_R"]},
            "H": {"protect": ap["avg_H"], "truncate": cp["avg_H"]},
            "coverage": {"protect": ap["avg_coverage"], "truncate": cp["avg_coverage"]},
            "path_len": {"protect": ap["avg_path_len"], "truncate": cp["avg_path_len"]},
            "path_len_matched": cov_match,
            "coverage_alive_vs_raw": cov_alive,
        }
    )

    # Secondary: protect_v2 vs truncate_v2
    av, cv = sm["A_protect_v2"], sm["C_truncate_v2"]
    mid_win_v = av["avg_mid_constraint_R"] >= cv["avg_mid_constraint_R"] + 0.15
    rh_v = av["avg_R"] >= cv["avg_R"] and av["avg_H"] >= cv["avg_H"] - 0.01
    status_v = (
        "supported"
        if mid_win_v and rh_v
        else ("mixed" if mid_win_v else "rejected")
    )
    verdicts.append(
        {
            "id": "RT2_protect_vs_truncate_v2",
            "status": status_v,
            "mid_R": {"protect": av["avg_mid_constraint_R"], "truncate": cv["avg_mid_constraint_R"]},
            "R": {"protect": av["avg_R"], "truncate": cv["avg_R"]},
            "H": {"protect": av["avg_H"], "truncate": cv["avg_H"]},
        }
    )

    # R near raw
    status_near = (
        "supported" if ap["avg_R"] >= raw["avg_R"] - 0.05 else "rejected"
    )
    verdicts.append(
        {
            "id": "RT2_protect_R_near_raw_mpH",
            "status": status_near,
            "protect_R": ap["avg_R"],
            "raw_R": raw["avg_R"],
            "delta": round(ap["avg_R"] - raw["avg_R"], 4),
        }
    )

    # Artifact: truncate must not fake-win solely via pool shrink
    fake = (
        cv["avg_H"] > av["avg_H"]
        and cv["avg_pool_n"] < av["avg_pool_n"] * 0.7
        and cv["avg_mid_constraint_R"] < 0.5
    )
    verdicts.append(
        {
            "id": "RT2_truncate_not_fake_win",
            "status": "artifact_risk" if fake else "ok",
            "truncate_H": cv["avg_H"],
            "protect_H": av["avg_H"],
            "pools": {"truncate": cv["avg_pool_n"], "protect": av["avg_pool_n"]},
        }
    )

    overall = "supported"
    if any(v["status"] == "rejected" for v in verdicts if v["id"].startswith("RT2_protect_vs")):
        overall = "mixed" if any(v["status"] in ("supported", "mixed", "mixed_strong_mid") for v in verdicts) else "rejected"
    if verdicts[0]["status"] in ("supported", "mixed_strong_mid"):
        overall = "supported" if verdicts[0]["status"] == "supported" else "mixed"
    elif verdicts[0]["status"] == "mixed":
        overall = "mixed"

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "experiment": "p0_rt2_protect_coverage_gated",
        "theory_ids": ["RT2", "P6"],
        "stamp": stamp,
        "promptdict_available": _PROMPTDICT,
        "config": {
            "n_hops": n_hops,
            "seed": seed,
            "n_seeds": n_seeds,
            "n_fixtures": n_fixtures,
            "budget": budget,
            "k": k,
            "elite_knobs": {"anchor_schedule": 2, "anchor_pull": 0.80, "select_by": "H"},
        },
        "summary_table": summary,
        "verdicts": verdicts,
        "overall_verdict": overall,
        "rows": rows,
    }

    jp = out_dir / f"rt2_coverage_gated_{stamp}.json"
    latest = out_dir / "rt2_coverage_gated_latest.json"
    text = json.dumps(payload, indent=2)
    jp.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")

    lines = [
        "# RT2 Protect-Compact → Burst (Coverage-Gated Redesign)",
        "",
        f"**Stamp:** {stamp} · PromptDict={_PROMPTDICT} · overall=**{overall}**",
        "",
        f"Config: fixtures={n_fixtures} seeds={n_seeds} hops={n_hops} budget={budget} k={k}",
        "",
        "| condition | C | R | H | mid_R | coverage | path_len | pool | tok |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in summary:
        lines.append(
            f"| {s['condition']} | {s['avg_C']:.3f} | {s['avg_R']:.3f} | {s['avg_H']:.3f} | "
            f"{s['avg_mid_constraint_R']:.3f} | {s['avg_coverage']:.3f} | {s['avg_path_len']:.2f} | "
            f"{s['avg_pool_n']:.1f} | {s['avg_tokens_after']:.0f} |"
        )
    lines.append("")
    lines.append("## Verdicts")
    for v in verdicts:
        lines.append(f"- **{v['id']}**: `{v['status']}` — `{json.dumps({k: v[k] for k in v if k not in ('id', 'status')}, default=str)}`")
    lines.append("")
    md_path = out_dir / f"rt2_coverage_gated_{stamp}.md"
    latest_md = out_dir / "rt2_coverage_gated_latest.md"
    md = "\n".join(lines) + "\n"
    md_path.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")

    # Simple chart if matplotlib present
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        chart_dir = out_dir / "charts"
        chart_dir.mkdir(parents=True, exist_ok=True)
        labels = [s["condition"].replace("_", "\n") for s in summary]
        x = range(len(summary))
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.bar([i - 0.2 for i in x], [s["avg_R"] for s in summary], width=0.2, label="R")
        ax.bar([i for i in x], [s["avg_H"] for s in summary], width=0.2, label="H")
        ax.bar(
            [i + 0.2 for i in x],
            [s["avg_mid_constraint_R"] for s in summary],
            width=0.2,
            label="mid_R",
        )
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, fontsize=7)
        ax.set_ylim(0, 1.05)
        ax.legend()
        ax.set_title("RT2 coverage-gated protect vs truncate")
        fig.tight_layout()
        cpath = chart_dir / "rt2_coverage_gated.png"
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
    print("\n=== RT2 coverage-gated protect->burst ===")
    print(f"overall={payload['overall_verdict']}  PromptDict={payload['promptdict_available']}")
    for s in payload["summary_table"]:
        print(
            f"{s['condition']:18s}  C={s['avg_C']:.3f} R={s['avg_R']:.3f} H={s['avg_H']:.3f} "
            f"mid_R={s['avg_mid_constraint_R']:.3f} cov={s['avg_coverage']:.3f}"
        )
    for v in payload["verdicts"]:
        print(f"  {v['id']}: {v['status']}")
    print(f"\nWrote {payload['paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
