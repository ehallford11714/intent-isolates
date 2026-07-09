# Typology

Each isolate receives a **TypologyLabel** with confidence and a short rationale.

## Labels

| Label | Meaning | Typical cues / signals |
|-------|---------|------------------------|
| `lexical` | Surface phrase / token bundle | Short spans, weak cues |
| `affective` | Emotion / valence | feel, afraid, anxious, hope |
| `instrumental` | Means / tool | using, via, method, tool |
| `confounder` | Spurious / common-cause role | confound, collider, proxy |
| `goal` | Desired end state | want, need, aim, goal |
| `constraint` | Bound / prohibition | cannot, unless, deadline |
| `action` | Executable step | submit, build, send, run |
| `outcome` | Result / effect | result, therefore, yields |
| `noise` | Filler / low signal | um, random, empty |
| `latent_feature` | Sparse / outlier dimension | high \|z\| or sparsity in features |
| `orphan_node` | Graph singleton / no edges | degree 0 component |
| `unknown` | No reliable cues | — |

## Classification policy

1. Kind priors (graph orphan → `orphan_node`; sparse feature → `latent_feature`)
2. Lexical cue scores + regex patterns
3. Layer prior (early → lexical; late → action/outcome)
4. Confidence is heuristic (`0.3–0.95`), not calibrated probability

## Relation to motifs

Typed motifs compose typology sequences, e.g.:

- `goal → constraint → action`
- `affective → instrumental → outcome`
- `lexical → latent_feature → goal`
