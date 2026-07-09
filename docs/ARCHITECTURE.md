# Architecture

`intentisolates` is a small, offline-first library in the intent stack.

```
text | features | graph
        │
        ▼
 identify_isolates  ──►  Isolate[]  (kind, label, span, layer, …)
        │
        ▼
 classify_typology  ──►  TypologyLabel + confidence + rationale
        │
        ▼
 assign_layers      ──►  abstract L0–L4 (or explicit / span / preserve)
        │
        ▼
 form_motifs        ──►  Motif[]  (co-occurrence, sequence, typed, chain, …)
        │
        ▼
 trajectory_from_motifs ──► ReasoningTrajectory (steps, mermaid, ASCII)
        │
        ▼
 IsolateReport (JSON / Markdown)
```

## Backends

| Backend | Dependency | Role |
|---------|------------|------|
| `rule` | none | Default; always works |
| `hf` | torch, transformers | Soft flag only in 0.2.0 (availability probe) |
| `llmintent` | llmintent | Soft layer-band hint / availability |
| `latentintent` | optional | Soft hook when package exists |

Rule results are never replaced by soft backends failing.

## Layers

Abstract reasoning layers (default):

| Id | Name | Typical isolates |
|----|------|------------------|
| 0 | L0_surface_lexical | lexical, noise |
| 1 | L1_semantic_binding | affective |
| 2 | L2_latent_workspace | latent_feature, confounder, orphan |
| 3 | L3_goal_constraint | goal, constraint, instrumental |
| 4 | L4_action_outcome | action, outcome |

When HF / llmintent hooks are available, callers may pass residual layer indices via `assign_layers(..., strategy="explicit", layer_map=...)`.

## Package layout

```
src/intentisolates/
  types.py          Isolate, Motif, ReasoningTrajectory, enums
  identify.py       identify_isolates
  typology.py       classify_typology
  layers.py         assign_layers + soft hooks
  motifs.py         form_motifs
  trajectory.py     trajectory_from_motifs
  report.py         IsolateReport builders
  cli.py            CLI
  backends/         availability probes
```

## Soft re-exports

- Prefer importing `intentisolates` directly (PyPI package).
- `llmintent.isolates` may soft-import this package when installed beside LLMIntent.
