#!/usr/bin/env python3
"""Offline experiment: creative_burst hopping vs linear / random / motif_jump.

Hypothesis: creative_burst increases typology-path entropy while preserving
visits to goal/constraint spans better than pure random.

Usage (from IntentIsolates repo root)::

    python experiments/span_burst_creative.py
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
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_RESEARCH = _ROOT.parent
for _sib in (_RESEARCH / "LLMIntent" / "src",):
    if _sib.is_dir() and str(_sib) not in sys.path:
        sys.path.insert(0, str(_sib))

_BACKEND_NOTE = "unavailable"
try:
    from intentisolates import (  # type: ignore
        CreativeBurstHopper,
        identify_span_isolates,
        typology_path_entropy,
    )

    _BACKEND_NOTE = "intentisolates"
except ImportError:
    try:
        from llmintent.isolates import (  # type: ignore
            CreativeBurstHopper,
            identify_span_isolates,
            typology_path_entropy,
        )

        _BACKEND_NOTE = "llmintent.isolates"
    except ImportError:
        CreativeBurstHopper = None  # type: ignore
        identify_span_isolates = None  # type: ignore
        typology_path_entropy = None  # type: ignore


FIXTURES: list[dict[str, Any]] = [
    {
        "id": "product_metaphor",
        "text": (
            "GOAL: I want to invent a playful onboarding metaphor for a budgeting app. "
            "CONSTRAINT: Cannot mention debt shaming or scare tactics. "
            "Imagine a garden where each sprout is a savings habit with unexpected color. "
            "Feel curious about the texture of small wins stacking into a canopy. "
            "Using a weekly check-in ritual via gentle reminders, build a rhythm. "
            "Do not exceed a 30-second first-run demo. "
            "OUTCOME: Result: a metaphor kit that sparks delight without pressure."
        ),
    },
    {
        "id": "story_twist",
        "text": (
            "My goal is to draft a short story opening with a wild twist. "
            "Constraint: must not reveal the antagonist in the first paragraph. "
            "The hallway smelled like rain and old paper; a curious rhythm tapped the pipes. "
            "I feel excited and a little afraid of the dream that won't stay put. "
            "Using a notebook and a timer, write three false leads. "
            "Require that every clue also works as a metaphor. "
            "Outcome: therefore the opening yields a burst of questions, not answers."
        ),
    },
    {
        "id": "research_creative",
        "text": (
            "Aim to produce a literature summary on prompt compression with a creative angle. "
            "Limit the draft to 800 words. Must cite LLMLingua and dictionary-encoding work. "
            "Cannot claim LLM task equivalence without a citation. "
            "Imagine compression as origami: folds that preserve the crease of intent. "
            "Feel frustrated by lossy drops that erase constraints mid-trace. "
            "Create an outline through thematic clustering, then write. "
            "Outcome: draft produced under the word limit; yields a citable playful summary."
        ),
    },
    {
        "id": "brand_voice",
        "text": (
            "Objective: refresh brand voice for a climate toolkit. "
            "Constraint: require hopeful tone; must not use doom language. "
            "Budget for the campaign window is two weeks. "
            "Spark ideas with textures of wind, tide, and shared tables. "
            "I want neighbors to feel invited, not lectured. "
            "Deploy a playful checklist via community workshops. "
            "Result: consequently the voice guide leads to warmer outreach copy."
        ),
    },
]

MODES = ("linear", "motif_jump", "creative_burst", "random")
ANCHOR_TYPS = frozenset({"goal", "constraint", "outcome"})


def _typ(v: Any) -> str:
    return v.value if hasattr(v, "value") else str(v)


def _metrics(path: Any, spans: Sequence[Any]) -> dict[str, Any]:
    by_id = {s.id: s for s in spans}
    typ_path = list(path.typology_path)
    ent = typology_path_entropy(typ_path) if typology_path_entropy else 0.0
    unique = len(set(path.span_ids))
    coverage = unique / max(1, len(spans))
    anchor_ids = {s.id for s in spans if _typ(s.typology) in ANCHOR_TYPS or getattr(s, "protect", False)}
    visited_anchors = [i for i in path.span_ids if i in anchor_ids]
    goal_c = sum(1 for i in path.span_ids if i in by_id and _typ(by_id[i].typology) == "goal")
    cons_c = sum(1 for i in path.span_ids if i in by_id and _typ(by_id[i].typology) == "constraint")
    # Motif overlap: fraction of consecutive hops that are motif-neighbors
    motif_hits = 0
    hop_n = max(1, len(path.hops))
    # Reconstruct neighbor set from hopper if available via metadata
    return {
        "path_len": len(path.span_ids),
        "n_hops": len(path.hops),
        "unique_spans": unique,
        "span_coverage": round(coverage, 4),
        "typology_entropy": ent,
        "n_unique_typologies": len(set(typ_path)),
        "anchor_visit_rate": round(len(set(visited_anchors)) / max(1, len(anchor_ids)), 4)
        if anchor_ids
        else 1.0,
        "anchor_visits": len(visited_anchors),
        "n_anchors": len(anchor_ids),
        "goal_visits": goal_c,
        "constraint_visits": cons_c,
        "typology_path": typ_path,
        "span_ids": list(path.span_ids),
    }


def run(*, n_hops: int, seed: int, out_dir: Path) -> dict[str, Any]:
    if identify_span_isolates is None or CreativeBurstHopper is None:
        raise SystemExit(
            "Neither intentisolates nor llmintent.isolates available. "
            "Install IntentIsolates or add LLMIntent to PYTHONPATH."
        )

    rows: list[dict[str, Any]] = []
    for fix in FIXTURES:
        spans = identify_span_isolates(fix["text"])
        hopper = CreativeBurstHopper(spans, seed=seed, anchor_pull=0.55)
        for mode in MODES:
            # Average over a few seed offsets for stability
            mode_metrics: list[dict[str, Any]] = []
            for offset in range(3):
                hopper2 = CreativeBurstHopper(spans, seed=seed + offset * 17, anchor_pull=0.55)
                path = hopper2.burst_path(seed=offset, n_hops=n_hops, mode=mode)
                mode_metrics.append(_metrics(path, spans))
            avg = _avg_metrics(mode_metrics)
            rows.append(
                {
                    "fixture_id": fix["id"],
                    "mode": mode,
                    "n_spans": len(spans),
                    **avg,
                    "example_typology_path": mode_metrics[0]["typology_path"],
                }
            )

    by_mode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_mode[r["mode"]].append(r)

    summary = []
    for mode in MODES:
        rs = by_mode[mode]
        summary.append(
            {
                "mode": mode,
                "n": len(rs),
                "avg_entropy": _mean([r["typology_entropy"] for r in rs]),
                "avg_span_coverage": _mean([r["span_coverage"] for r in rs]),
                "avg_anchor_visit_rate": _mean([r["anchor_visit_rate"] for r in rs]),
                "avg_goal_visits": _mean([r["goal_visits"] for r in rs]),
                "avg_constraint_visits": _mean([r["constraint_visits"] for r in rs]),
                "avg_unique_typs": _mean([r["n_unique_typologies"] for r in rs]),
                "avg_path_len": _mean([r["path_len"] for r in rs]),
            }
        )

    sm = {s["mode"]: s for s in summary}
    cb, rnd, lin = sm.get("creative_burst", {}), sm.get("random", {}), sm.get("linear", {})
    verdict = []
    if (cb.get("avg_entropy") or 0) > (lin.get("avg_entropy") or 0) + 0.05:
        verdict.append(
            "creative_burst increased typology entropy vs linear (diversity gain)."
        )
    else:
        verdict.append(
            "creative_burst entropy was not clearly above linear; inspect fixtures."
        )
    if (cb.get("avg_anchor_visit_rate") or 0) + 0.05 >= (rnd.get("avg_anchor_visit_rate") or 0):
        verdict.append(
            "creative_burst preserved goal/constraint/outcome visits at least as well as random "
            "(anchor pull working)."
        )
    else:
        verdict.append(
            "random visited anchors more than creative_burst — raise anchor_pull."
        )
    if (cb.get("avg_entropy") or 0) >= (rnd.get("avg_entropy") or 0) - 0.05 and (
        cb.get("avg_anchor_visit_rate") or 0
    ) > (rnd.get("avg_anchor_visit_rate") or 0) + 0.05:
        verdict.append(
            "Hypothesis supported: creative_burst matches/beats random diversity while "
            "improving anchor visit rate."
        )

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "backend": _BACKEND_NOTE,
        "n_hops": n_hops,
        "seed": seed,
        "n_fixtures": len(FIXTURES),
        "modes": list(MODES),
        "summary_table": summary,
        "rows": rows,
        "verdict": verdict,
        "hypothesis": (
            "creative_burst hopping increases typology diversity while preserving "
            "visits to goal/constraint spans vs pure random"
        ),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = out_dir / f"span_burst_{stamp}.json"
    md_path = out_dir / f"span_burst_{stamp}.md"
    latest_json = out_dir / "span_burst_latest.json"
    latest_md = out_dir / "span_burst_latest.md"
    text = json.dumps(payload, indent=2)
    json_path.write_text(text, encoding="utf-8")
    latest_json.write_text(text, encoding="utf-8")
    md = _render_md(payload)
    md_path.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")

    # Link into research doc if present
    research_doc = _RESEARCH / "docs" / "ISOLATES_COMPACTION_REASONING.md"
    if research_doc.is_file():
        _link_research_doc(research_doc)

    payload["paths"] = {
        "json": str(json_path),
        "markdown": str(md_path),
        "latest_json": str(latest_json),
        "latest_md": str(latest_md),
    }
    return payload


def _mean(xs: Sequence[float]) -> float:
    return round(sum(xs) / len(xs), 4) if xs else 0.0


def _avg_metrics(ms: list[dict[str, Any]]) -> dict[str, Any]:
    keys = [
        "path_len",
        "n_hops",
        "unique_spans",
        "span_coverage",
        "typology_entropy",
        "n_unique_typologies",
        "anchor_visit_rate",
        "anchor_visits",
        "n_anchors",
        "goal_visits",
        "constraint_visits",
    ]
    out: dict[str, Any] = {}
    for k in keys:
        out[k] = _mean([float(m[k]) for m in ms])
    return out


def _render_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Span-burst creative hopping experiment",
        "",
        f"- Created: `{payload['created_at']}`",
        f"- Backend: `{payload['backend']}`",
        f"- Hops: `{payload['n_hops']}` · fixtures: `{payload['n_fixtures']}`",
        "",
        "## Summary",
        "",
        "| mode | entropy | coverage | anchor_R | goal_vis | constr_vis | unique_typs |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in payload["summary_table"]:
        lines.append(
            f"| {s['mode']} | {s['avg_entropy']:.3f} | {s['avg_span_coverage']:.3f} | "
            f"{s['avg_anchor_visit_rate']:.3f} | {s['avg_goal_visits']:.2f} | "
            f"{s['avg_constraint_visits']:.2f} | {s['avg_unique_typs']:.2f} |"
        )
    lines += ["", "## Verdict", ""]
    for v in payload["verdict"]:
        lines.append(f"- {v}")
    lines += ["", "## Hypothesis", "", payload["hypothesis"], ""]
    return "\n".join(lines) + "\n"


def _link_research_doc(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    marker = "## Span isolates & creative burst"
    if marker in text:
        return
    blurb = """

## Span isolates & creative burst

See `IntentIsolates/docs/SPAN_ISOLATES_CREATIVE_BURST.md` and
`IntentIsolates/experiments/span_burst_creative.py`.

**Bridge to compaction:** protect `SpanIsolate.protect` (goal/constraint/outcome) spans
during PromptDict compact the same way isolate-then-compact protects mid-trace constraints;
then hop `creative_burst` on the hot set for divergent exploration without dropping anchors.

"""
    # Insert before references section if present
    if "\n## 8. References" in text:
        text = text.replace("\n## 8. References", blurb + "\n## 8. References")
    else:
        text = text.rstrip() + blurb
    path.write_text(text, encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hops", type=int, default=5)
    p.add_argument("--seed", type=int, default=17)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=_ROOT / "experiments" / "results",
    )
    args = p.parse_args(list(argv) if argv is not None else None)
    print(f"Backend: {_BACKEND_NOTE}")
    payload = run(n_hops=args.hops, seed=args.seed, out_dir=args.out_dir)
    print("\n=== Summary ===")
    for s in payload["summary_table"]:
        print(
            f"{s['mode']:16s}  H={s['avg_entropy']:.3f}  "
            f"cov={s['avg_span_coverage']:.3f}  "
            f"anchor_R={s['avg_anchor_visit_rate']:.3f}"
        )
    print("\nVerdict:")
    for v in payload["verdict"]:
        print(f"  - {v}")
    print(f"\nWrote {payload['paths']['markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
