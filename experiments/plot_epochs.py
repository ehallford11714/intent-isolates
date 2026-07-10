#!/usr/bin/env python3
"""Plot iterative epoch trajectory (C/R/H vs epoch).

Usage::

    python experiments/plot_epochs.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

_ROOT = Path(__file__).resolve().parents[1]
_EPOCHS = _ROOT / "experiments" / "results" / "iterative_epochs"
_CHARTS = _ROOT / "experiments" / "results" / "charts"


def main() -> int:
    traj_path = _EPOCHS / "trajectory_latest.json"
    if not traj_path.is_file():
        print(f"Missing {traj_path}", file=sys.stderr)
        return 1
    traj = json.loads(traj_path.read_text(encoding="utf-8"))
    epochs = traj["epochs"]
    xs = [e["epoch"] for e in epochs]
    C = [e["avg_C"] for e in epochs]
    R = [e["avg_R"] for e in epochs]
    H = [e["avg_H"] for e in epochs]
    guides = [e["guided_by"] for e in epochs]

    _CHARTS.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.plot(xs, C, "o-", label="C", color="#4C78A8", linewidth=2)
    ax.plot(xs, R, "s-", label="R", color="#F58518", linewidth=2)
    ax.plot(xs, H, "^-", label="H", color="#54A24B", linewidth=2)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Score")
    ax.set_title("RT-guided iterative training: C / R / H vs epoch")
    ax.set_xticks(xs)
    ax.set_ylim(0.5, 1.0)
    ax.grid(True, alpha=0.25, linestyle="--")
    ax.legend(loc="best")
    # annotate RT phases
    for x, g in zip(xs, guides):
        ax.annotate(g, (x, min(H) - 0.02), fontsize=7, ha="center", color="#555555", rotation=45)
    fig.tight_layout()
    out = _CHARTS / "epoch_crh_trajectory.png"
    fig.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")

    # knobs secondary chart: H with mono
    mono = [e["avg_layer_mono"] for e in epochs]
    mid = [e["avg_mid_constraint_R"] for e in epochs]
    fig2, ax2 = plt.subplots(figsize=(10, 4.5))
    ax2.plot(xs, H, "^-", label="H", color="#54A24B", linewidth=2)
    ax2.plot(xs, mono, "d-", label="layer_mono", color="#B279A2", linewidth=2)
    ax2.plot(xs, mid, "x-", label="mid_constraint_R", color="#E45756", linewidth=2)
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Score")
    ax2.set_title("H, layer_mono, mid_constraint_R vs epoch")
    ax2.set_xticks(xs)
    ax2.grid(True, alpha=0.25, linestyle="--")
    ax2.legend(loc="best")
    fig2.tight_layout()
    out2 = _CHARTS / "epoch_h_mono_mid.png"
    fig2.savefig(out2, dpi=140, bbox_inches="tight")
    plt.close(fig2)
    print(f"Wrote {out2}")

    # update CHARTS.md pointer
    charts_md = _ROOT / "experiments" / "results" / "CHARTS.md"
    blurb = (
        f"\n## Iterative epochs ({traj.get('stamp', '')})\n\n"
        f"- ![epoch CRH](charts/epoch_crh_trajectory.png)\n"
        f"- ![epoch H/mono/mid](charts/epoch_h_mono_mid.png)\n"
        f"- Trajectory: [EPOCH_TRAJECTORY.md](iterative_epochs/EPOCH_TRAJECTORY.md)\n"
    )
    if charts_md.is_file():
        text = charts_md.read_text(encoding="utf-8")
        if "epoch_crh_trajectory.png" not in text:
            charts_md.write_text(text.rstrip() + "\n" + blurb, encoding="utf-8")
    else:
        charts_md.write_text("# Charts\n" + blurb, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
