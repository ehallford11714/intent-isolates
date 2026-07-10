#!/usr/bin/env python3
"""Plot IntentIsolates / PromptDict experiment results into PNG charts.

Reads latest JSON under experiments/results/ (and sibling PromptDictCompress
compaction results when present). Writes PNG + CHARTS.md index.

Usage::

    python experiments/plot_results.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

_ROOT = Path(__file__).resolve().parents[1]
_RESULTS = _ROOT / "experiments" / "results"
_CHARTS = _RESULTS / "charts"
_RESEARCH = _ROOT.parent
_COMPACT = _RESEARCH / "PromptDictCompress" / "experiments" / "results"


def _load(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#333333",
            "axes.labelcolor": "#222222",
            "text.color": "#222222",
            "xtick.color": "#333333",
            "ytick.color": "#333333",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
        }
    )


def _save(fig: plt.Figure, name: str) -> Path:
    _CHARTS.mkdir(parents=True, exist_ok=True)
    path = _CHARTS / name
    fig.tight_layout()
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return path


def chart_lit_crh(lit: dict[str, Any]) -> Path | None:
    rows = lit.get("summary_table") or []
    if not rows:
        return None
    labels = [r["condition"] for r in rows]
    C = [r["avg_C"] for r in rows]
    R = [r["avg_R"] for r in rows]
    H = [r["avg_H"] for r in rows]
    x = range(len(labels))
    w = 0.27
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.bar([i - w for i in x], C, width=w, label="C", color="#4C78A8")
    ax.bar(list(x), R, width=w, label="R", color="#F58518")
    ax.bar([i + w for i in x], H, width=w, label="H", color="#54A24B")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Lit-burst: CreativityMeter C / R / H by condition")
    ax.legend(frameon=False)
    return _save(fig, "lit_burst_C_R_H.png")


def chart_lit_structure(lit: dict[str, Any]) -> Path | None:
    rows = lit.get("summary_table") or []
    if not rows:
        return None
    labels = [r["condition"] for r in rows]
    ent = [r["avg_entropy"] for r in rows]
    anc = [r["avg_anchor_R"] for r in rows]
    mono = [r["avg_layer_mono"] for r in rows]
    x = range(len(labels))
    w = 0.27
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.bar([i - w for i in x], ent, width=w, label="entropy", color="#72B7B2")
    ax.bar(list(x), anc, width=w, label="anchor_R", color="#E45756")
    ax.bar([i + w for i in x], mono, width=w, label="layer_mono", color="#B279A2")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_ylabel("Metric")
    ax.set_title("Lit-burst: entropy / anchor_R / layer_monotonicity")
    ax.legend(frameon=False)
    return _save(fig, "lit_burst_entropy_anchor_mono.png")


def chart_v1_v2_multipath(lit: dict[str, Any]) -> Path | None:
    sm = {r["condition"]: r for r in lit.get("summary_table") or []}
    keys = ["creative_burst_v1", "creative_burst_v2", "multipath_tot"]
    if not all(k in sm for k in keys):
        # theory sweep names
        alt = ["creative_burst_v1", "creative_burst_v2", "multipath_k5_H"]
        if all(k in sm for k in alt):
            keys = alt
        else:
            return None
    metrics = ["avg_C", "avg_R", "avg_H", "avg_anchor_R"]
    metric_labels = ["C", "R", "H", "anchor_R"]
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    x = range(len(metrics))
    w = 0.25
    colors = ["#9D755D", "#4C78A8", "#54A24B"]
    for i, cond in enumerate(keys):
        vals = [sm[cond][m] for m in metrics]
        ax.bar([j + (i - 1) * w for j in x], vals, width=w, label=cond, color=colors[i])
    ax.set_xticks(list(x))
    ax.set_xticklabels(metric_labels)
    ax.set_ylim(0, 1.05)
    ax.set_title("v1 vs v2 vs multipath comparison")
    ax.legend(frameon=False)
    return _save(fig, "v1_v2_multipath_compare.png")


def chart_span_burst(span: dict[str, Any]) -> Path | None:
    rows = span.get("summary_table") or []
    if not rows:
        return None
    labels = [r["mode"] for r in rows]
    ent = [r["avg_entropy"] for r in rows]
    anc = [r["avg_anchor_visit_rate"] for r in rows]
    x = range(len(labels))
    w = 0.35
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar([i - w / 2 for i in x], ent, width=w, label="entropy", color="#72B7B2")
    ax.bar([i + w / 2 for i in x], anc, width=w, label="anchor_R", color="#E45756")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_title("Span-burst modes: entropy vs anchor_R")
    ax.legend(frameon=False)
    return _save(fig, "span_burst_entropy_anchor.png")


def chart_compaction(comp: dict[str, Any]) -> Path | None:
    rows = comp.get("summary_table") or comp.get("summary") or []
    # prompt dict format may use different keys
    if not rows and "by_condition" in comp:
        rows = comp["by_condition"]
    if not rows:
        # try nested
        for k in ("averages", "conditions_summary"):
            if isinstance(comp.get(k), list):
                rows = comp[k]
                break
    if not rows:
        return None
    # normalize
    labels, mid, motif = [], [], []
    for r in rows:
        labels.append(r.get("condition") or r.get("mode") or r.get("name") or "?")
        mid.append(
            float(
                r.get("avg_mid_constraint_recall_visible")
                or r.get("mid_R_vis")
                or r.get("avg_mid_constraint_R")
                or r.get("mid_constraint_R")
                or 0
            )
        )
        motif.append(
            float(
                r.get("avg_motif_jaccard")
                or r.get("motif_J")
                or r.get("motif_jaccard")
                or 0
            )
        )
    x = range(len(labels))
    w = 0.35
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar([i - w / 2 for i in x], mid, width=w, label="mid_constraint_R", color="#F58518")
    ax.bar([i + w / 2 for i in x], motif, width=w, label="motif_J", color="#4C78A8")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_title("Compaction: mid-constraint recall vs motif Jaccard")
    ax.legend(frameon=False)
    return _save(fig, "compaction_mid_constraint_motif.png")


def chart_theory_crh(sweep: dict[str, Any]) -> Path | None:
    rows = sweep.get("summary_table") or []
    if not rows:
        return None
    # sort by H desc, show top 12 for readability
    rows = sorted(rows, key=lambda r: -r["avg_H"])[:12]
    labels = [r["condition"] for r in rows]
    C = [r["avg_C"] for r in rows]
    R = [r["avg_R"] for r in rows]
    H = [r["avg_H"] for r in rows]
    x = range(len(labels))
    w = 0.27
    fig, ax = plt.subplots(figsize=(13, 5.5))
    ax.bar([i - w for i in x], C, width=w, label="C", color="#4C78A8")
    ax.bar(list(x), R, width=w, label="R", color="#F58518")
    ax.bar([i + w for i in x], H, width=w, label="H", color="#54A24B")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=40, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_title("Theory corpus sweep (top-12 by H): C / R / H")
    ax.legend(frameon=False)
    return _save(fig, "theory_sweep_C_R_H_top12.png")


def chart_p0_e1(p0: dict[str, Any]) -> Path | None:
    rows = (p0.get("E1") or {}).get("summary_table") or []
    if not rows:
        return None
    # Focus k=5 and k=7 value functions
    focus = [r for r in rows if r.get("k") in (5, 7)]
    if not focus:
        focus = rows
    labels = [r["condition"] for r in focus]
    C = [r["avg_C"] for r in focus]
    R = [r["avg_R"] for r in focus]
    H = [r["avg_H"] for r in focus]
    x = range(len(labels))
    w = 0.27
    fig, ax = plt.subplots(figsize=(13, 5.2))
    ax.bar([i - w for i in x], C, width=w, label="C", color="#4C78A8")
    ax.bar(list(x), R, width=w, label="R", color="#F58518")
    ax.bar([i + w for i in x], H, width=w, label="H", color="#54A24B")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("P0 E1: Multipath value-function bakeoff (C / R / H)")
    ax.legend(frameon=False)
    return _save(fig, "p0_e1_multipath_value_fn.png")


def chart_p0_e2(p0: dict[str, Any]) -> Path | None:
    rows = (p0.get("E2") or {}).get("summary_table") or []
    if not rows:
        return None
    labels = [r["condition"] for r in rows]
    R = [r["avg_R"] for r in rows]
    H = [r["avg_H"] for r in rows]
    mid = [r["avg_mid_constraint_R"] for r in rows]
    x = range(len(labels))
    w = 0.27
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar([i - w for i in x], R, width=w, label="R", color="#F58518")
    ax.bar(list(x), H, width=w, label="H", color="#54A24B")
    ax.bar([i + w for i in x], mid, width=w, label="mid_R", color="#E45756")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("P0 E2: Protect-compact → burst (R / H / mid_constraint_R)")
    ax.legend(frameon=False)
    return _save(fig, "p0_e2_protect_burst.png")


def chart_p0_e3(p0: dict[str, Any]) -> Path | None:
    rows = (p0.get("E3") or {}).get("summary_table") or []
    if not rows:
        return None
    # One grouped chart for hops=8 primary (longer horizon) + hops=5 if present
    hop8 = [r for r in rows if r.get("n_hops") == 8]
    use = hop8 if hop8 else rows
    labels = [r["condition"] for r in use]
    C = [r["avg_C"] for r in use]
    R = [r["avg_R"] for r in use]
    H = [r["avg_H"] for r in use]
    x = range(len(labels))
    w = 0.27
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar([i - w for i in x], C, width=w, label="C", color="#4C78A8")
    ax.bar(list(x), R, width=w, label="R", color="#F58518")
    ax.bar([i + w for i in x], H, width=w, label="H", color="#54A24B")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylim(0, 1.05)
    hops = use[0].get("n_hops", "?")
    ax.set_ylabel("Score")
    ax.set_title(f"P0 E3: Structured incubation vs controls (hops={hops})")
    ax.legend(frameon=False)
    return _save(fig, "p0_e3_structured_incubation.png")


def chart_claims(sweep: dict[str, Any]) -> Path | None:
    counts = sweep.get("evidence_counts") or {}
    if not counts:
        return None
    labels = ["supported", "rejected", "mixed", "untested"]
    sizes = [int(counts.get(k, 0)) for k in labels]
    if sum(sizes) == 0:
        return None
    colors = ["#54A24B", "#E45756", "#F58518", "#9D9D9D"]
    fig, ax = plt.subplots(figsize=(6.5, 5))
    wedges, *_ = ax.pie(
        sizes,
        labels=[f"{l}\n({s})" for l, s in zip(labels, sizes)],
        colors=colors,
        startangle=90,
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    ax.set_title("Claim evidence verdicts (theory_corpus_sweep)")
    return _save(fig, "claim_evidence_verdicts.png")


def main() -> int:
    _style()
    written: list[tuple[str, Path]] = []

    lit = _load(_RESULTS / "lit_burst_latest.json")
    span = _load(_RESULTS / "span_burst_latest.json")
    sweep = _load(_RESULTS / "theory_corpus_sweep_latest.json")
    compact = _load(_COMPACT / "reasoning_compaction_latest.json")
    p0 = _load(_RESULTS / "p0_followup_latest.json")

    if lit:
        for fn, title in (
            (chart_lit_crh, "Lit-burst C/R/H"),
            (chart_lit_structure, "Lit-burst entropy/anchor/mono"),
            (chart_v1_v2_multipath, "v1 vs v2 vs multipath"),
        ):
            p = fn(lit)
            if p:
                written.append((title, p))
    if span:
        p = chart_span_burst(span)
        if p:
            written.append(("Span-burst entropy vs anchor_R", p))
    if compact:
        p = chart_compaction(compact)
        if p:
            written.append(("Compaction mid_R vs motif_J", p))
    if sweep:
        p = chart_theory_crh(sweep)
        if p:
            written.append(("Theory sweep top-12 C/R/H", p))
        p = chart_claims(sweep)
        if p:
            written.append(("Claim evidence pie", p))
        # also v1/v2/multipath from sweep if lit missing keys
        if not lit:
            p = chart_v1_v2_multipath(sweep)
            if p:
                written.append(("v1 vs v2 vs multipath (sweep)", p))
    if p0:
        for fn, title in (
            (chart_p0_e1, "P0 E1 multipath value-fn"),
            (chart_p0_e2, "P0 E2 protect→burst"),
            (chart_p0_e3, "P0 E3 structured incubation"),
        ):
            p = fn(p0)
            if p:
                written.append((title, p))

    # CHARTS.md index
    lines = [
        "# Experiment charts",
        "",
        "Regenerate: `python experiments/plot_results.py`",
        "",
        f"Sources: `lit_burst_latest.json`, `span_burst_latest.json`, "
        f"`theory_corpus_sweep_latest.json`, `p0_followup_latest.json`, "
        f"PromptDictCompress `reasoning_compaction_latest.json`.",
        "",
    ]
    if not written:
        lines.append("_No charts generated — missing result JSON files._")
    for title, path in written:
        rel = path.relative_to(_RESULTS).as_posix()
        lines += [f"## {title}", "", f"![{title}]({rel})", "", f"`{path.name}`", ""]
    index = _RESULTS / "CHARTS.md"
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(written)} charts -> {_CHARTS}")
    for title, path in written:
        print(f"  - {path.name}: {title}")
    print(f"Index: {index}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
