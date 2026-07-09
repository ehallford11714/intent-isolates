# Layer motifs ↔ IV / AutoCausal

Bridge **IntentIsolates** layer motifs with **AutoCausal** / **CausalIV** so you can
separate **indication** (association) from **causation** (instrumental variables).

Package surface: `intentisolates.causal` · CLI: `python -m intentisolates causal`

## Pipeline

```
text / features / graph
        │
        ▼
 identify_isolates → typology → abstract layers L0–L4
        │
        ▼
 form_motifs  +  trajectory_from_motifs
        │
        ▼
 build_feature_frame   →  columns like isolate_goal_L3, motif_typed_path_L1_…
        │
        ├─► estimate_indication  (Pearson |r| with Y)     = layer indication
        └─► estimate_layer_iv    (Z=lower, X=mid/late→Y) = layer causation
```

## IV design on layers

| Role | Typical layers | Meaning |
|------|----------------|---------|
| **Z** (instrument) | L0–L1 (lexical / affective / early) | Candidate exogenous shifter of mid-layer structure |
| **X** (endogenous) | L2–L4 (latent / goal / action) | Motif or isolate hypothesized to affect output |
| **Y** (outcome) | derived | From outcome/action/goal isolates, or `--outcome-hint` / user vector |

Estimator preference (soft imports):

1. `causaliv.estimate_2sls` (CausalIVSuite)
2. `autocausal.iv._numpy_2sls` (AutoCausalLib lite)
3. Stdlib Wald IV `β = Cov(Z,Y) / Cov(Z,X)`
4. `--mock-iv` for offline tests

## API

```python
from intentisolates.causal import LayerCausalSuite

suite = LayerCausalSuite.from_text(
    "I want to finish the report. I cannot miss the deadline. "
    "I feel anxious. I will submit it using the portal so that it is on time."
)
result = suite.run(outcome_hint="on time")

print(result.to_markdown())
# Indication: high |r| for late-layer action/outcome features with Y
# Causation:  motif@L2 → Y with β_IV, instrumented by isolate_affective_L1
```

Feature table only:

```python
from intentisolates import identify_isolates, form_motifs
from intentisolates.causal import build_feature_frame, estimate_indication, estimate_layer_iv

isos = identify_isolates(text="...")
motifs = form_motifs(isos)
table = build_feature_frame(isos, motifs, outcome_hint="decision")
ind = estimate_indication(table)
edges, notes = estimate_layer_iv(table)
```

## CLI (primary)

```bash
python -m intentisolates causal --text "..." --outcome-hint decision
python -m intentisolates causal --text "..." --format json -o report.json
python -m intentisolates causal --text "..." --mock-iv   # tests / no causaliv
```

Soft mirror when AutoCausalLib is installed:

```bash
python -m autocausal isolates-causal --text "..."
```

## Example: indication vs causation

| Layer | Indication (max \|r\|) | Causation (max \|β_IV\|) | Reading |
|-------|------------------------|---------------------------|---------|
| L1 affective | 0.42 | — (used as Z) | **Indicates** Y; treated as instrument, not cause |
| L2 latent motif | 0.31 | 0.55 (Z=L1) | Associates **and** IV-supported effect on Y |
| L4 action | 0.61 | 0.12 (weak F) | Strong indication; weak/uncertain causation |

A layer can **indicate** Y without **causing** it (confounding / common cause).
IV recovers causation only under relevance + exclusion; bootstrap rows from one
text are **exploratory**, not population inference.

## Epistemic caveats

- **Indication ≠ causation.** Association matrices are descriptive.
- **IV assumptions:** Z relevant for X; Z affects Y only through X; no open
  back-door from Z to Y. These are rarely verified for abstract L0–L4 scaffolds.
- **Weak instruments** (low first-stage F) bias β_IV toward OLS — flagged on edges.
- **Abstract layers** are a reasoning scaffold unless bound to residual-stream indices
  (optional `llmintent` / LatentIntentInspect hooks).
- Motifs remain **structural hypotheses**, not proven cognitive mechanisms.

## Related packages

- [IntentIsolates](../README.md) — isolates, motifs, trajectories
- AutoCausalLib — `autocausal.iv`, discover, mine
- CausalIVSuite — `causaliv.estimate_2sls`, validate
