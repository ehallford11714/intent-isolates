# Next Experiments: Higher Cognition + Causal/Kineteq Bridge

**Status:** prioritized queue (scripts named for later implementation)  
**Theory:** [THEORY_HIGHER_COGNITION_GROUNDING.md](THEORY_HIGHER_COGNITION_GROUNDING.md) · [THEORY_CAUSAL_KINETEQ_BRIDGE.md](THEORY_CAUSAL_KINETEQ_BRIDGE.md)  
**Baseline:** `experiments/results/lit_burst_latest.md` — multipath_tot best \(H\); v2 lifts \(R\)

Offline-automatable preferred. Success criteria are relative to **creative_burst_v2** and **multipath_tot** unless noted.

---

## P0 — ship next (adjudicate core cognition + compact)

### E1 — `goal_neglect_under_compact`
- **Script:** `experiments/goal_neglect_compact_burst.py`
- **Theory:** WM goal maintenance / Baddeley–Miyake (P6)
- **Protocol:** For each fixture: (a) protect_compact + `filter_spans_for_burst` + v2; (b) truncate/drop-protect + v2; (c) no compact baseline.
- **Metrics:** `anchor_R`, `constraint_fidelity`, \(R\), \(H\`; flag `goal_neglect_under_compact` in JSON when protect goals missing from path.
- **Success:** (a) `anchor_R` ≥ (b) by ≥0.10; (a) \(R\) ≥ no-compact − 0.05.
- **Effort:** S

### E2 — `two_phase_diverge_converge`
- **Script:** `experiments/two_phase_set_shift_burst.py`
- **Theory:** Dual-process + task-switching (P1 refinement)
- **Protocol:** First ⌊n/2⌋ hops divergent knobs; second half convergent/anchor; compare to pure v2 / multipath.
- **Metrics:** \(C\), \(R\), \(H\), entropy trajectory, switch cost.
- **Success:** Two-phase \(H\) ≥ v2; \(C\) within 0.05 of divergent on first half.
- **Effort:** S

### E3 — `conflict_adaptive_anchor_schedule`
- **Script:** `experiments/conflict_monitor_anchor.py`
- **Theory:** Botvinick conflict monitoring (P7)
- **Protocol:** Trigger forced protect visit when rolling typology entropy high or `anchor_need` exceeds threshold; vs fixed `anchor_schedule=3`.
- **Metrics:** \(H\), `anchor_R`, number of forced visits.
- **Success:** Adaptive \(H\) ≥ fixed on ≥3/4 fixtures without \(C\) collapse >0.05.
- **Effort:** S–M

---

## P1 — cognition depth + causal bridge

### E4 — `planning_depth_layer_tol`
- **Script:** `experiments/tower_london_layer_planning.py`
- **Theory:** Soar/ACT-R planning; ToL analog (P3)
- **Protocol:** Require visiting goal/constraint before action/outcome (layer order check); vary hop budget 3–9.
- **Metrics:** plan success rate, `layer_mono`, \(H\).
- **Success:** `layer_cot` / multipath plan success > divergent by ≥15 pp at budget 5.
- **Effort:** M

### E5 — `burst_proposed_instruments_iv`
- **Script:** `experiments/burst_instruments_vs_random_iv.py`
- **Theory:** Bridge B1; explore \(Z\) vs random; LayerCausal + causaliv soft
- **Protocol:** From burst path, propose early-layer spans as \(Z\); mid/late as \(X\); compare to random Z assignment; mock-IV allowed for CI.
- **Metrics:** first-stage F (or proxy), \(|\beta_{IV}|\), SE, weak-IV rate.
- **Success:** Burst-Z mean F > random-Z; weak-IV rate ≤ random.
- **Effort:** M

### E6 — `indication_vs_causation_alignment`
- **Script:** `experiments/path_R_vs_layer_causation.py`
- **Theory:** Bridge B2 / P10; diagnosticity of hops
- **Protocol:** Correlate path \(R\) (and \(C\)) with overlap between visited features and top causation vs indication edges from `LayerCausalSuite`.
- **Metrics:** Spearman(\(R\), causation-overlap); Spearman(\(C\), indication-overlap).
- **Success:** \(R\) correlates more with causation-overlap than \(C\) does; \(C\) may track indication.
- **Effort:** M

### E7 — `multipath_then_causal_validate`
- **Script:** `experiments/multipath_H_then_iv_validate.py`
- **Theory:** GWT broadcast + B4
- **Protocol:** k=5 multipath select-by-\(H\); run IV validate on winner vs random path vs best-\(C\) path.
- **Metrics:** edge quality, weak-IV, placebo pass; \(H\) of selected path.
- **Success:** H-winner ≥ best-\(C\) on validation pass rate; ≥ random.
- **Effort:** M

---

## P2 — orchestration + transfer

### E8 — `compact_protect_then_iv`
- **Script:** `experiments/compact_protect_iv_pipeline.py`
- **Theory:** Bridge B3; compaction doc
- **Protocol:** protect_compact → feature frame on survivors → IV; vs truncate mid-spans → IV.
- **Metrics:** retained valid edges, `constraint_fidelity`, indication/causation matrices stability.
- **Success:** Protect pipeline retains ≥20% more non-weak edges than truncate.
- **Effort:** M

### E9 — `analogical_transfer_fixtures`
- **Script:** `experiments/motif_transfer_cross_fixture.py`
- **Theory:** Gentner structure-mapping (P9)
- **Protocol:** Fit motif priors on fixture A; hop on B with/without prior.
- **Metrics:** transfer \(R\), motif reuse rate, \(H\).
- **Success:** With-prior \(R\) > cold start on B.
- **Effort:** M

### E10 — `bridge_kineteq_route_stub`
- **Script:** `experiments/orchestration_broadcast_dryrun.py`
- **Theory:** GWT + Bridge B5; Kineteq-style route
- **Protocol:** Offline: map high-\(H\) path → recommended next tool enum `{iv_validate, search_ground, remine, pivot_guide}`; compare to random; optional CausalBridge `dry_run` if present; record `kineteq_backend` from guide probe.
- **Metrics:** route rubric score (hand rules), artifact schema OK.
- **Success:** Meter-gated rubric > random by ≥0.2; never routes `iv_validate` when \(R\) < threshold.
- **Effort:** L (can stub rubric-only first as M)

---

## Deferred / optional

| Idea | Why later |
| --- | --- |
| Meter-guided MCTS/beam | Needs value-fn plumbing beyond multipath |
| Online LLM rescoring of hops | Expensive; not offline-default |
| GoT merge-to-goal hops | P2 research in CREATIVE_BURST_IMPROVEMENTS |
| Live Kineteq MCP | Requires external bus credentials |

---

## Results schema flags (light)

When implementing, include in JSON results:

```json
{
  "goal_neglect_under_compact": false,
  "orchestration_stage": "burst_explore",
  "kineteq_backend": "absent",
  "theory_ids": ["P6", "B3"]
}
```

Optional package note (no heavy module required): document the same stage names under `docs/` or a one-file `src/intentisolates/orchestration_stages.py` constants list if touching code.

---

## Priority summary

| Priority | Experiments | Adjudicates |
| --- | --- | --- |
| **P0** | E1–E3 | WM protect, dual-process schedule, conflict control |
| **P1** | E4–E7 | Planning depth, instrument explore, R↔causation, multipath+IV |
| **P2** | E8–E10 | Compact→IV, analogical transfer, Bridge/Kineteq broadcast |

Run order recommendation: **E1 → E2 → E5 → E6 → E7 → E3 → E4 → E8 → E9 → E10**.
