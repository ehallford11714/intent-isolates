# Claim evidence table (theory_corpus_sweep)

- Created: `2026-07-10T00:08:41.803667+00:00`
- Counts: **{'supported': 24, 'rejected': 4, 'mixed': 1, 'untested': 0}**

| ID | Prediction | Metrics | Verdict | Strength |
| --- | --- | --- | --- | --- |
| P1a | H(v2)>H(random) | mean_a=0.7520 mean_b=0.6986 Δ=0.0534 wins=7/8 | **supported** | strong |
| P1b | C(v2) within 0.05 of C(random) | C(v2)=0.7283, C(rand)=0.7118, |Δ|=0.0165 | **supported** | moderate |
| P2 | anchor_R(v2)>anchor_R(random) | mean_a=0.8958 mean_b=0.7257 Δ=0.1701 wins=7/8 | **supported** | strong |
| P3 | mono(layer_cot)>=mono(divergent) | mean_a=0.6333 mean_b=0.5750 Δ=0.0583 wins=7/8 | **supported** | strong |
| P4a | C(div)>C(conv) | mean_a=0.7644 mean_b=0.6533 Δ=0.1111 wins=8/8 | **supported** | strong |
| P4b | entropy(div)>=entropy(conv) | mean_a=2.4183 mean_b=1.9874 Δ=0.4309 wins=8/8 | **supported** | strong |
| P5 | H(multipath_H)>=H(v2) | mean_a=0.7697 mean_b=0.7520 Δ=0.0177 wins=8/8 | **supported** | moderate |
| P6a | protect_hotset R >= truncate R | mean_a=0.8049 mean_b=0.8522 Δ=-0.0473 wins=3/8 | **rejected** | moderate |
| P6b | protect_hotset anchor_R >= truncate | mean_a=0.9062 mean_b=1.0000 Δ=-0.0938 wins=4/8 | **mixed** | weak |
| P7 | conflict_sched H >= v2 H | mean_a=0.7588 mean_b=0.7520 Δ=0.0068 wins=6/8 | **supported** | moderate |
| P8a | sidehop C >= convergent C | mean_a=0.7515 mean_b=0.6533 Δ=0.0982 wins=8/8 | **supported** | strong |
| P8b | sidehop R not much below convergent (delta>-0.08) | R(side)=0.7605, R(conv)=0.8963, Δ=-0.1358 | **rejected** | weak |
| L1a | motif R > v2 R | mean_a=0.9005 mean_b=0.7923 Δ=0.1082 wins=6/8 | **supported** | moderate |
| L1b | motif C < v2 C | mean_a=0.5643 mean_b=0.7283 Δ=-0.1640 wins=8/8 | **supported** | strong |
| L2 | v2 R > v1 R | mean_a=0.7923 mean_b=0.7535 Δ=0.0388 wins=5/8 | **supported** | moderate |
| G1 | mp_H R >= mp_C R | mean_a=0.8375 mean_b=0.7373 Δ=0.1002 wins=8/8 | **supported** | strong |
| G2 | k5 H >= k3 H | mean_a=0.7697 mean_b=0.7649 Δ=0.0048 wins=8/8 | **supported** | moderate |
| G3 | k7 H >= k5 H | mean_a=0.7739 mean_b=0.7697 Δ=0.0042 wins=8/8 | **supported** | moderate |
| PP1 | precision_high R >= precision_low R | mean_a=0.8817 mean_b=0.7069 Δ=0.1748 wins=7/8 | **supported** | strong |
| PP2 | precision_low C >= precision_high C | mean_a=0.7684 mean_b=0.6777 Δ=0.0907 wins=8/8 | **supported** | strong |
| I1 | incubation H >= divergent H | mean_a=0.6917 mean_b=0.7295 Δ=-0.0378 wins=1/8 | **rejected** | moderate |
| I2 | two_phase H >= v2 H | mean_a=0.7237 mean_b=0.7520 Δ=-0.0283 wins=0/8 | **rejected** | weak |
| PL1 | layer_cot H >= divergent H | mean_a=0.7457 mean_b=0.7295 Δ=0.0162 wins=5/8 | **supported** | moderate |
| S1 | v2 H >= linear H | mean_a=0.7520 mean_b=0.6377 Δ=0.1143 wins=8/8 | **supported** | strong |
| S2 | v1 entropy >= linear | mean_a=2.3627 mean_b=1.9312 Δ=0.4315 wins=7/8 | **supported** | strong |
| S3 | motif mono >= divergent mono | mean_a=0.9750 mean_b=0.5750 Δ=0.4000 wins=8/8 | **supported** | strong |
| B4 | mp_H R >= random R | mean_a=0.8375 mean_b=0.6963 Δ=0.1412 wins=7/8 | **supported** | strong |
| B1 | burst path mean first_stage_F >= random (mock IV) | F(burst)=4.2025 F(random)=4.2025 | **supported** | weak |
| B2 | high-R (convergent) causation_overlap >= divergent | cau_ov(conv)=0.0000 cau_ov(div)=0.0000 | **supported** | weak |

---

## P0 follow-up append (2026-07-10, `p0_followup_20260710T002719Z`)

| ID | Prediction | Metrics | Verdict | Strength |
| --- | --- | --- | --- | --- |
| P13a | select-by-H ≥ R/C on H (k=3,5,7) | k7 H=0.776 best; 8/8 each k | **supported** | strong |
| P13b | select-by-R ≥ H/C on R | k5 R=0.850 > H 0.829; ΔH≈−0.011 | **supported** | strong |
| P13c / G1 | select-by-H ≥ C on R | k5 ΔR=+0.085; k7 +0.111; 8/8 | **supported** | strong |
| P13d | iv_diag H≥H−0.01 and R≥H-select | k5 fail (H=0.760); k7 pass (H=0.772,R=0.862) | **mixed** | moderate |
| P15a | protect mid_R ≥0.95 ≫ truncate | mid_R 1.000 vs 0.188 | **supported** | strong |
| P15b | protect→mpH R ≥ truncate R | R 0.897 ≥ 0.851; H mixed (trunc artifact) | **mixed** | moderate |
| P15c | protect→v2 R ≥ raw−0.05 | R 0.886 ≥ 0.799 | **supported** | strong |
| P17 / E3 | structured incub H ≥ v2 (hops 5,8) | H 0.686/0.695 ≪ 0.754/0.790; 0/8 | **rejected** | strong |
