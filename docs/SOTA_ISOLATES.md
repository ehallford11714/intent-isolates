# SOTA notes: isolates (research)

Short survey with caveats. This library implements **offline heuristics**, not full SAE / community-detection pipelines.

## Monosemanticity / SAE features

Sparse autoencoders (Anthropic, etc.) aim to decompose activations into more monosemantic features. A high-sparsity, high-|z| dimension in our `features` path is only a **proxy** for a “feature isolate” — not a trained SAE dictionary atom.

**Caveat:** Without a trained dictionary and eval harness, “latent_feature” labels are hypotheses.

## Community detection / graph isolates

In network science, isolates are degree-0 nodes; singleton components are a related notion. Causal graphs similarly surface variables with no edges. Our graph path flags orphans and leaves.

**Caveat:** Real causal discovery needs identification assumptions; we only report structural isolation.

## Linguistic isolates

In linguistics, an isolate language has no proven relatives. By analogy, a lexical isolate here is a separable intent phrase. Clause splitting + cue lexicons are a crude stand-in for semantic parsing.

**Caveat:** Not multilingual-robust; English cue lists dominate.

## Causal isolation

Causal isolation (no parents/children, or singleton components) is useful for screening confounders vs. detached variables. Typed motifs like `goal→constraint→action` are narrative templates, not do-calculus.

## Motifs in interpretability

Circuit / motif language in mech-interp (induction heads, skip trigrams) inspires our motif vocabulary. Co-occurrence and typed paths are **analogues**, not circuit proofs.

## Layers and trajectories

Residual-stream analyses often assign early/mid/late functional roles. Our L0–L4 scaffold mirrors that pedagogy for **intent** units so motifs can be read as trajectories. Soft hooks to `llmintent` layer maps exist when installed.

**Caveat:** Do not equate abstract layers with a specific model’s block index without an explicit mapping.
