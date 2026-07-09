# Claim evidence table (theory_corpus_sweep)

- Created: `2026-07-09T23:50:36.644494+00:00`
- Counts: **{'supported': 24, 'rejected': 5, 'mixed': 0, 'untested': 0}**

| ID | Prediction | Metrics | Verdict | Strength |
| --- | --- | --- | --- | --- |
| P1a | H(v2)>H(random) | mean_a=0.7538 mean_b=0.6995 Δ=0.0543 wins=7/8 | **supported** | strong |
| P1b | C(v2) within 0.05 of C(random) | C(v2)=0.7281, C(rand)=0.6781, |Δ|=0.0500 | **supported** | moderate |
| P2 | anchor_R(v2)>anchor_R(random) | mean_a=0.8858 mean_b=0.7262 Δ=0.1596 wins=7/8 | **supported** | strong |
| P3 | mono(layer_cot)>=mono(divergent) | mean_a=0.6550 mean_b=0.5850 Δ=0.0700 wins=8/8 | **supported** | strong |
| P4a | C(div)>C(conv) | mean_a=0.7608 mean_b=0.6575 Δ=0.1033 wins=8/8 | **supported** | strong |
| P4b | entropy(div)>=entropy(conv) | mean_a=2.4016 mean_b=2.0107 Δ=0.3909 wins=8/8 | **supported** | strong |
| P5 | H(multipath_H)>=H(v2) | mean_a=0.7693 mean_b=0.7538 Δ=0.0155 wins=8/8 | **supported** | moderate |
| P6a | protect_hotset R >= truncate R | mean_a=0.7987 mean_b=0.8460 Δ=-0.0473 wins=3/8 | **rejected** | moderate |
| P6b | protect_hotset anchor_R >= truncate | mean_a=0.8896 mean_b=1.0000 Δ=-0.1104 wins=3/8 | **rejected** | moderate |
| P7 | conflict_sched H >= v2 H | mean_a=0.7635 mean_b=0.7538 Δ=0.0097 wins=5/8 | **supported** | moderate |
| P8a | sidehop C >= convergent C | mean_a=0.7393 mean_b=0.6575 Δ=0.0818 wins=8/8 | **supported** | strong |
| P8b | sidehop R not much below convergent (delta>-0.08) | R(side)=0.7773, R(conv)=0.903, Δ=-0.1257 | **rejected** | weak |
| L1a | motif R > v2 R | mean_a=0.8996 mean_b=0.7963 Δ=0.1033 wins=5/8 | **supported** | moderate |
| L1b | motif C < v2 C | mean_a=0.5658 mean_b=0.7281 Δ=-0.1623 wins=8/8 | **supported** | strong |
| L2 | v2 R > v1 R | mean_a=0.7963 mean_b=0.7544 Δ=0.0419 wins=5/8 | **supported** | moderate |
| G1 | mp_H R >= mp_C R | mean_a=0.8362 mean_b=0.7342 Δ=0.1020 wins=8/8 | **supported** | strong |
| G2 | k5 H >= k3 H | mean_a=0.7693 mean_b=0.7676 Δ=0.0017 wins=8/8 | **supported** | moderate |
| G3 | k7 H >= k5 H | mean_a=0.7738 mean_b=0.7693 Δ=0.0045 wins=8/8 | **supported** | moderate |
| PP1 | precision_high R >= precision_low R | mean_a=0.8908 mean_b=0.7398 Δ=0.1510 wins=8/8 | **supported** | strong |
| PP2 | precision_low C >= precision_high C | mean_a=0.7550 mean_b=0.6709 Δ=0.0841 wins=8/8 | **supported** | strong |
| I1 | incubation H >= divergent H | mean_a=0.6906 mean_b=0.7335 Δ=-0.0429 wins=1/8 | **rejected** | moderate |
| I2 | two_phase H >= v2 H | mean_a=0.7285 mean_b=0.7538 Δ=-0.0253 wins=1/8 | **rejected** | weak |
| PL1 | layer_cot H >= divergent H | mean_a=0.7578 mean_b=0.7335 Δ=0.0243 wins=7/8 | **supported** | moderate |
| S1 | v2 H >= linear H | mean_a=0.7538 mean_b=0.6517 Δ=0.1021 wins=8/8 | **supported** | strong |
| S2 | v1 entropy >= linear | mean_a=2.3516 mean_b=2.0249 Δ=0.3267 wins=7/8 | **supported** | strong |
| S3 | motif mono >= divergent mono | mean_a=0.9800 mean_b=0.5850 Δ=0.3950 wins=8/8 | **supported** | strong |
| B4 | mp_H R >= random R | mean_a=0.8362 mean_b=0.7398 Δ=0.0964 wins=7/8 | **supported** | strong |
| B1 | burst path mean first_stage_F >= random (mock IV) | F(burst)=4.2025 F(random)=4.2025 | **supported** | weak |
| B2 | high-R (convergent) causation_overlap >= divergent | cau_ov(conv)=0.0000 cau_ov(div)=0.0000 | **supported** | weak |
