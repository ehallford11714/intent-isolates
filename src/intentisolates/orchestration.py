"""Orchestration stage names for Causal Fabric / Kineteq-style loops.

Thin constants only — not a full control plane. See
``docs/THEORY_CAUSAL_KINETEQ_BRIDGE.md``. CausalBridge workflows remain the
runtime orchestrator; this module labels experiment/result stages.
"""

from __future__ import annotations

from typing import Any

# Pipeline stages (mine → explore → compact → estimate → ground → route)
STAGE_MINE_ISOLATE = "mine_isolate"
STAGE_BURST_EXPLORE = "burst_explore"
STAGE_COMPACT_PROTECT = "compact_protect"
STAGE_IV_ESTIMATE = "iv_estimate"
STAGE_GROUND_RECALL = "ground_recall"
STAGE_BRIDGE_ROUTE = "bridge_route"

STAGES: tuple[str, ...] = (
    STAGE_MINE_ISOLATE,
    STAGE_BURST_EXPLORE,
    STAGE_COMPACT_PROTECT,
    STAGE_IV_ESTIMATE,
    STAGE_GROUND_RECALL,
    STAGE_BRIDGE_ROUTE,
)

# Result-schema flags used by higher-cognition / bridge experiments
FLAG_GOAL_NEGLECT_UNDER_COMPACT = "goal_neglect_under_compact"
FLAG_KINETEQ_BACKEND = "kineteq_backend"
FLAG_ORCHESTRATION_STAGE = "orchestration_stage"
FLAG_THEORY_IDS = "theory_ids"

KINETEQ_BACKEND_ABSENT = "absent"
KINETEQ_BACKEND_PIVOT_FALLBACK = "pivot_fallback"
KINETEQ_BACKEND_MCP = "kineteq_mcp"
KINETEQ_BACKEND_MODULE = "kineteq_module"


def orchestration_meta(
    *,
    stage: str = STAGE_BURST_EXPLORE,
    goal_neglect_under_compact: bool = False,
    kineteq_backend: str = KINETEQ_BACKEND_ABSENT,
    theory_ids: list[str] | None = None,
    select_by: str = "tradeoff_harmonic",
) -> dict[str, Any]:
    """Build a small dict suitable for merging into experiment JSON results."""
    if stage not in STAGES:
        raise ValueError(f"unknown stage {stage!r}; expected one of {STAGES}")
    return {
        FLAG_ORCHESTRATION_STAGE: stage,
        FLAG_GOAL_NEGLECT_UNDER_COMPACT: bool(goal_neglect_under_compact),
        FLAG_KINETEQ_BACKEND: kineteq_backend,
        FLAG_THEORY_IDS: list(theory_ids or []),
        "select_by": select_by,
    }


__all__ = [
    "STAGES",
    "STAGE_MINE_ISOLATE",
    "STAGE_BURST_EXPLORE",
    "STAGE_COMPACT_PROTECT",
    "STAGE_IV_ESTIMATE",
    "STAGE_GROUND_RECALL",
    "STAGE_BRIDGE_ROUTE",
    "FLAG_GOAL_NEGLECT_UNDER_COMPACT",
    "FLAG_KINETEQ_BACKEND",
    "FLAG_ORCHESTRATION_STAGE",
    "FLAG_THEORY_IDS",
    "KINETEQ_BACKEND_ABSENT",
    "KINETEQ_BACKEND_PIVOT_FALLBACK",
    "KINETEQ_BACKEND_MCP",
    "KINETEQ_BACKEND_MODULE",
    "orchestration_meta",
]
