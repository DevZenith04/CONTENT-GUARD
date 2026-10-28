# ADR 0005: Choice of unitary/toxic-bert for Local Inference

## Context
Running real-time content moderation requires local execution capabilities without incurring per-token cloud API bills or streaming latency. The model must run efficiently on commodity CPUs without specialized GPU acceleration.

## Decision
We select `unitary/toxic-bert` (fine-tuned DistilBERT) for multi-label toxicity classification. It outputs calibrated probabilities across 6 labels: `toxic`, `severe_toxic`, `obscene`, `threat`, `insult`, and `identity_hate`.

## Known Limitations & Mitigation
1. **Domain Contamination**: The model was trained on Wikipedia/Jigsaw toxicity corpora. Benchmarking strictly against Jigsaw would yield contaminated results; we evaluate on an independent curated dataset.
2. **Missing Self-Harm Head**: The model lacks a dedicated self-harm classification head. We supplement this via keyword heuristics and generalized distress signaling until a fine-tuned head is introduced.
3. **Severe Toxic Mapping**: `severe_toxic` represents intense abuse/harassment and is mapped to `harassment`, reserving `threat` for physical violence.

## Consequences
- **Positive**: Lightweight (~260MB), fast CPU inference (~25ms), completely offline, zero API costs.
- **Negative**: Requires 512-token input truncation and cannot replace generative contextual reasoning on subtle sarcasm without fine-tuning.
