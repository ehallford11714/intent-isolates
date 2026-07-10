# Epoch Trajectory (RT-guided iterative training)

**Stamp:** 20260710T001218Z · **Epochs:** 10 · **R floor:** 0.78

## Epoch → RT map

| Epoch | guided_by | phase | note |
| ---: | --- | --- | --- |
| 0 | baseline | floor_v2_single | Default creative_burst_v2 knobs, no multipath |
| 1 | baseline | floor_multipath_H | Enable multipath k=5 select_by=H (P5/G2 floor) |
| 2 | RT1 | value_fn_bakeoff | Mutate select_by / k; elite by H with R floor |
| 3 | RT1 | value_fn_refine | Keep elite selection rule; small k/select refinement |
| 4 | RT2 | protect_on | Turn protect_compact filter on; mid_constraint + H |
| 5 | RT2 | protect_toggle | Compare protect on vs off; keep better on H/R/mid |
| 6 | RT4 | conflict_schedule | Grid anchor_schedule / anchor_pull (P7 conflict) |
| 7 | RT5 | layer_mono | Raise layer_bias toward mono without motif C-collapse |
| 8 | RT3 | iv_diag_or_hybrid | Prefer iv_diag select or hybrid RT1+RT2 elite knobs |
| 9 | RT3 | hybrid_polish | Final hill-climb on novelty/anchor/layer around elite |

## Metrics by epoch

| epoch | RT | C | R | H | anchor_R | layer_mono | mid_R | accepted |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | baseline | 0.702 | 0.828 | 0.753 | 0.950 | 0.600 | 1.000 | schedule_multipath |
| 1 | baseline | 0.712 | 0.840 | 0.766 | 0.933 | 0.667 | 1.000 | k7_H |
| 2 | RT1 | 0.710 | 0.846 | 0.768 | 0.933 | 0.683 | 1.000 | keep |
| 3 | RT1 | 0.710 | 0.846 | 0.768 | 0.933 | 0.683 | 1.000 | keep |
| 4 | RT2 | 0.710 | 0.846 | 0.768 | 0.933 | 0.683 | 1.000 | protect_on |
| 5 | RT2 | 0.709 | 0.858 | 0.772 | 0.933 | 0.717 | 1.000 | protect_on_anchor+ |
| 6 | RT4 | 0.695 | 0.897 | 0.779 | 0.950 | 0.800 | 1.000 | keep |
| 7 | RT5 | 0.695 | 0.897 | 0.779 | 0.950 | 0.800 | 1.000 | keep |
| 8 | RT3 | 0.695 | 0.897 | 0.779 | 0.950 | 0.800 | 1.000 | layer- |
| 9 | RT3 | 0.696 | 0.897 | 0.779 | 0.950 | 0.800 | 1.000 | — |

**Best epoch:** 9 (H=0.779, R=0.897, C=0.696)

## Knobs (initial → final → best)

```json
{
  "initial": {
    "novelty_weight": 1.1,
    "anchor_pull": 0.7,
    "layer_bias": 0.55,
    "motif_weight": 0.45,
    "anchor_schedule": 3,
    "side_hop_prob": 0.18,
    "multipath": false,
    "k": 5,
    "select_by": "H",
    "protect_compact": false,
    "soft_mono_gate": false
  },
  "final": {
    "novelty_weight": 1.1,
    "anchor_pull": 0.7999999999999999,
    "layer_bias": 0.47000000000000003,
    "motif_weight": 0.45,
    "anchor_schedule": 2,
    "side_hop_prob": 0.18,
    "multipath": true,
    "k": 7,
    "select_by": "H",
    "protect_compact": true,
    "soft_mono_gate": false
  },
  "best": {
    "novelty_weight": 1.1,
    "anchor_pull": 0.7999999999999999,
    "layer_bias": 0.47000000000000003,
    "motif_weight": 0.45,
    "anchor_schedule": 2,
    "side_hop_prob": 0.18,
    "multipath": true,
    "k": 7,
    "select_by": "H",
    "protect_compact": true,
    "soft_mono_gate": false
  }
}
```

## Update rule

- Maximize mean **H** with soft **R** floor.
- Each epoch's search neighborhood is dictated by RT phase (see map).
- Eligible variants evaluated on the same fixtures×seeds; elite kept.
