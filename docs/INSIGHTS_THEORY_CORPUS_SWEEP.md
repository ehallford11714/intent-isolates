# Insights: Theory Corpus Sweep (2026-07-09)

**Sweep:** `experiments/results/theory_corpus_sweep_20260709T235036Z`  
**Evidence table:** [CLAIM_EVIDENCE_TABLE.md](../experiments/results/CLAIM_EVIDENCE_TABLE.md)  
**Full report:** [COMPREHENSIVE_EXPERIMENTAL_FINDINGS_REPORT.md](COMPREHENSIVE_EXPERIMENTAL_FINDINGS_REPORT.md)

## Counts

| supported | rejected | mixed | untested |
| ---: | ---: | ---: | ---: |
| 24 | 5 | 0 | 0 |

## Inventory highlights

- **Supported (moderate+):** P1–P5 (core burst), dual-process P4, precision PP1/PP2, GWT G1–G3, motif L1, v2>v1 L2, layer_cot PL1/P3, conflict P7, side-hop C (P8a), baselines S1–S3, B4 (multipath R≥random).
- **Rejected:** P6 WM protect≥truncate (sim artifact), P8b side-hop R tax, I1 incubation, I2 two-phase.
- **Weak causal:** B1/B2 flagged supported but strength=weak (mock IV / zero overlap).

## Production takeaway

Keep `for_v2` defaults; prefer multipath select-by-H; do not ship incubation/two-phase or aggressive side_hop until redesigned.
