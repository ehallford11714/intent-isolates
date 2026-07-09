"""intentisolates — identify isolates, typology, motifs, and reasoning trajectories."""

from __future__ import annotations

from intentisolates.identify import identify_isolates
from intentisolates.layers import assign_layers, soft_latentintent_layers, soft_llmintent_layers
from intentisolates.motifs import form_motifs
from intentisolates.report import build_report, report_to_json, report_to_markdown
from intentisolates.span_burst import (
    CreativeBurstHopper,
    burst_path_from_text,
    identify_span_isolates,
    span_isolates_from_isolates,
    typology_path_entropy,
)
from intentisolates.trajectory import trajectory_from_motifs
from intentisolates.types import (
    ABSTRACT_LAYERS,
    BurstHop,
    BurstPath,
    Isolate,
    IsolateKind,
    IsolateReport,
    Motif,
    MotifTypology,
    ReasoningTrajectory,
    SpanIsolate,
    TextSpan,
    TrajectoryRole,
    TrajectoryStep,
    TypologyLabel,
)
from intentisolates.typology import classify_typology
from intentisolates.backends import available_backends

__version__ = "0.4.0"

__all__ = [
    "__version__",
    "ABSTRACT_LAYERS",
    "BurstHop",
    "BurstPath",
    "CreativeBurstHopper",
    "Isolate",
    "IsolateKind",
    "IsolateReport",
    "LayerCausalResult",
    "LayerCausalSuite",
    "Motif",
    "MotifTypology",
    "ReasoningTrajectory",
    "SpanIsolate",
    "TextSpan",
    "TrajectoryRole",
    "TrajectoryStep",
    "TypologyLabel",
    "assign_layers",
    "available_backends",
    "build_report",
    "burst_path_from_text",
    "classify_typology",
    "form_motifs",
    "identify_isolates",
    "identify_span_isolates",
    "report_to_json",
    "report_to_markdown",
    "soft_latentintent_layers",
    "soft_llmintent_layers",
    "span_isolates_from_isolates",
    "trajectory_from_motifs",
    "typology_path_entropy",
]


def __getattr__(name: str):
    if name in ("LayerCausalSuite", "LayerCausalResult"):
        from intentisolates.causal import LayerCausalResult, LayerCausalSuite

        return LayerCausalSuite if name == "LayerCausalSuite" else LayerCausalResult
    raise AttributeError(f"module 'intentisolates' has no attribute {name!r}")
