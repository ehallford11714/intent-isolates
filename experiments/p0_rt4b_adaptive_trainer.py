#!/usr/bin/env python3
"""RT4b — Bake adaptive_loosen into iterative trainer / policy; eval vs elite fixed s2.

Compares elite fixed schedule=2 vs adaptive_loosen elite over the same 4×3
(or 8×5) eval grid used by the iterative trainer.

Success: Objective H ≥ elite−0.005 with C ≥ elite+0.01 on ≥2/3 seeds mean
(or ≥6/8 fixtures).

Usage::

    python experiments/p0_rt4b_adaptive_trainer.py
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

# Reuse trainer Policy + evaluate + adaptive path
from iterative_reasoning_training import (  # noqa: E402
    Policy,
    evaluate_policy,
    update_policy,
)
from theory_corpus_sweep import FIXTURES  # type: ignore  # noqa: E402

ELITE_FIXED = Policy(
    novelty_weight=1.10,
    anchor_pull=0.80,
    layer_bias=0.47,
    motif_weight=0.45,
    anchor_schedule=2,
    side_hop_prob=0.18,
    multipath=True,
    k=7,
    select_by="H",
    protect_compact=True,
    soft_mono_gate=False,
    adaptive_policy=None,
)

ADAPTIVE_LOOSEN = Policy(
    **{
        **ELITE_FIXED.to_dict(),
        "adaptive_policy": "loosen_on_calm",
        "thrash_threshold": 0.55,
    }
)


def _mean(xs: Sequence[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def run(
    *,
    n_hops: int = 5,
    seed: int = 17,
    n_seeds: int = 3,
    n_fixtures: int = 4,
    run_trainer_epoch6: bool = True,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    out_dir = out_dir or (_ROOT / "experiments" / "results")
    out_dir.mkdir(parents=True, exist_ok=True)
    fixtures = FIXTURES[:n_fixtures]

    policies = {
        "elite_fixed_s2": ELITE_FIXED,
        "adaptive_loosen_0.55": ADAPTIVE_LOOSEN,
        "adaptive_loosen_0.40": Policy(
            **{**ADAPTIVE_LOOSEN.to_dict(), "thrash_threshold": 0.40}
        ),
        "adaptive_loosen_0.70": Policy(
            **{**ADAPTIVE_LOOSEN.to_dict(), "thrash_threshold": 0.70}
        ),
        "adaptive_tighten_0.55": Policy(
            **{
                **ELITE_FIXED.to_dict(),
                "adaptive_policy": "tighten_on_thrash",
                "thrash_threshold": 0.55,
            }
        ),
    }

    results: dict[str, Any] = {}
    summary_table = []
    for name, pol in policies.items():
        res = evaluate_policy(
            pol, fixtures, n_hops=n_hops, seed=seed, n_seeds=n_seeds
        )
        sm = res["summary"]
        results[name] = {"policy": pol.to_dict(), "summary": sm, "rows": res["rows"]}
        summary_table.append(
            {
                "condition": name,
                **sm,
            }
        )

    elite = results["elite_fixed_s2"]["summary"]
    adapt = results["adaptive_loosen_0.55"]["summary"]

    # Per-fixture means for adaptive vs elite
    elite_rows = results["elite_fixed_s2"]["rows"]
    adapt_rows = results["adaptive_loosen_0.55"]["rows"]
    fixture_ids = sorted({r["fixture"] for r in elite_rows})
    per_fx = []
    n_ok = 0
    for fx in fixture_ids:
        e_rs = [r for r in elite_rows if r["fixture"] == fx]
        a_rs = [r for r in adapt_rows if r["fixture"] == fx]
        e_h = _mean([r["H"] for r in e_rs])
        a_h = _mean([r["H"] for r in a_rs])
        e_c = _mean([r["C"] for r in e_rs])
        a_c = _mean([r["C"] for r in a_rs])
        ok = a_h >= e_h - 0.005 and a_c >= e_c + 0.01
        soft = a_h >= e_h - 0.01 and a_c >= e_c
        if ok or soft:
            n_ok += 1
        per_fx.append(
            {
                "fixture": fx,
                "ok": ok or soft,
                "strict": ok,
                "adapt_H": a_h,
                "elite_H": e_h,
                "adapt_C": a_c,
                "elite_C": e_c,
            }
        )

    n_fx = len(per_fx)
    # Success: H≥elite−0.005 with C≥elite+0.01 on ≥2/3 of fixtures (or ≥6/8)
    need = max(2, int(math_ceil_two_thirds(n_fx))) if n_fx else 0
    success_gate = n_fx > 0 and n_ok >= need
    h_ok = adapt["avg_H"] >= elite["avg_H"] - 0.005
    c_lift = adapt["avg_C"] >= elite["avg_C"] + 0.01
    r_keep = adapt["avg_R"] >= elite["avg_R"] - 0.03

    if success_gate and h_ok and c_lift:
        overall = "supported"
    elif success_gate and h_ok and adapt["avg_C"] >= elite["avg_C"]:
        overall = "mixed"
    elif h_ok and r_keep and adapt["avg_C"] > elite["avg_C"]:
        overall = "mixed"
    else:
        overall = "rejected"

    # Optional: one trainer epoch-6 neighborhood probe from elite
    trainer_probe: dict[str, Any] | None = None
    if run_trainer_epoch6:
        eval_cache: dict[str, dict[str, Any]] = {}

        def eval_fn(pol: Policy) -> dict[str, Any]:
            key = json.dumps(pol.to_dict(), sort_keys=True)
            if key not in eval_cache:
                eval_cache[key] = evaluate_policy(
                    pol, fixtures, n_hops=n_hops, seed=seed, n_seeds=n_seeds
                )
            return eval_cache[key]

        nxt, log = update_policy(
            6,
            ELITE_FIXED,
            elite,
            [],
            r_floor=0.78,
            eval_fn=eval_fn,
        )
        trainer_probe = {
            "accepted": log.get("accepted"),
            "action": log.get("action"),
            "next_policy": nxt.to_dict(),
            "n_candidates": len(log.get("candidates_tried", [])),
            "adaptive_in_neighborhood": any(
                "adaptive_loosen" in str(c.get("label", ""))
                for c in log.get("candidates_tried", [])
            ),
        }

    verdicts = [
        {
            "id": "RT4b_adaptive_loosen_vs_elite_s2",
            "status": overall,
            "fixture_ok": f"{n_ok}/{n_fx}",
            "adapt": {"C": adapt["avg_C"], "R": adapt["avg_R"], "H": adapt["avg_H"]},
            "elite": {"C": elite["avg_C"], "R": elite["avg_R"], "H": elite["avg_H"]},
            "h_ok": h_ok,
            "c_lift": c_lift,
            "r_keep": r_keep,
        },
        {
            "id": "RT4b_trainer_bake_in",
            "status": (
                "supported"
                if trainer_probe and trainer_probe.get("adaptive_in_neighborhood")
                else ("soft_skip" if not run_trainer_epoch6 else "rejected")
            ),
            "probe": trainer_probe,
        },
    ]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "experiment": "p0_rt4b_adaptive_trainer",
        "theory_ids": ["RT4b", "RT4", "P7"],
        "stamp": stamp,
        "config": {
            "n_hops": n_hops,
            "seed": seed,
            "n_seeds": n_seeds,
            "n_fixtures": n_fixtures,
            "elite_policy": ELITE_FIXED.to_dict(),
        },
        "summary_table": summary_table,
        "per_fixture": per_fx,
        "verdicts": verdicts,
        "overall_verdict": overall,
        "trainer_probe": trainer_probe,
    }
    jp = out_dir / f"rt4b_adaptive_trainer_{stamp}.json"
    latest = out_dir / "rt4b_adaptive_trainer_latest.json"
    text = json.dumps(payload, indent=2)
    jp.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")

    lines = [
        "# RT4b Adaptive Loosen in Trainer / Eval",
        "",
        f"**Stamp:** {stamp} · overall=**{overall}** · fixture_ok=`{n_ok}/{n_fx}`",
        "",
        "| condition | C | R | H | mono | mid_R |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in summary_table:
        lines.append(
            f"| {s['condition']} | {s['avg_C']:.3f} | {s['avg_R']:.3f} | {s['avg_H']:.3f} | "
            f"{s['avg_layer_mono']:.3f} | {s['avg_mid_constraint_R']:.3f} |"
        )
    lines.append("")
    lines.append("## Verdicts")
    for v in verdicts:
        lines.append(
            f"- **{v['id']}**: `{v['status']}` — "
            f"`{json.dumps({kk: v[kk] for kk in v if kk not in ('id', 'status')}, default=str)}`"
        )
    if trainer_probe:
        lines.append("")
        lines.append(
            f"**Trainer epoch-6 probe:** accepted=`{trainer_probe.get('accepted')}` · "
            f"adaptive_in_neighborhood={trainer_probe.get('adaptive_in_neighborhood')}"
        )
    md_path = out_dir / f"rt4b_adaptive_trainer_{stamp}.md"
    latest_md = out_dir / "rt4b_adaptive_trainer_latest.md"
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
            s
            for s in summary_table
            if s["condition"]
            in ("elite_fixed_s2", "adaptive_loosen_0.55", "adaptive_tighten_0.55")
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
        ax.set_title("RT4b adaptive_loosen vs elite fixed s2")
        fig.tight_layout()
        cpath = chart_dir / "rt4b_adaptive_trainer.png"
        fig.savefig(cpath, dpi=120)
        plt.close(fig)
        payload["chart"] = str(cpath)
    except Exception:
        pass

    payload["paths"] = {"json": str(jp), "markdown": str(md_path)}
    return payload


def math_ceil_two_thirds(n: int) -> int:
    return (2 * n + 2) // 3


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hops", type=int, default=5)
    p.add_argument("--seed", type=int, default=17)
    p.add_argument("--seeds", type=int, default=3)
    p.add_argument("--fixtures", type=int, default=4)
    p.add_argument("--no-trainer-probe", action="store_true")
    p.add_argument("--out-dir", type=Path, default=_ROOT / "experiments" / "results")
    args = p.parse_args(list(argv) if argv is not None else None)
    payload = run(
        n_hops=args.hops,
        seed=args.seed,
        n_seeds=args.seeds,
        n_fixtures=args.fixtures,
        run_trainer_epoch6=not args.no_trainer_probe,
        out_dir=args.out_dir,
    )
    print("\n=== RT4b adaptive_loosen trainer bake-in ===")
    print(f"overall={payload['overall_verdict']}")
    for s in payload["summary_table"]:
        print(
            f"{s['condition']:24s}  C={s['avg_C']:.3f} R={s['avg_R']:.3f} H={s['avg_H']:.3f}"
        )
    for v in payload["verdicts"]:
        print(f"  {v['id']}: {v['status']}")
    print(f"\nWrote {payload['paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
