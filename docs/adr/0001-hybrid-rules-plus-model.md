# ADR 0001: Hybrid Rules Plus Transformer Architecture

## Context
Online content moderation systems face a fundamental trade-off between deterministic precision, latency, and contextual comprehension. Pure keyword/regex heuristics are fast (sub-millisecond) but suffer from high false positive rates on benign idioms and cannot interpret nuanced hostility. Conversely, deep transformer models capture semantic context and sarcasm well, but incur higher inference latency and can hallucinate or fluctuate across boundary thresholds.

## Decision
We adopt a **Hybrid Pipeline Architecture**:
1. **Rule Engine**: Evaluates fast regex and keyword patterns first.
2. **Contextual Transformer (`unitary/toxic-bert`)**: Evaluates input semantics offloaded to worker threads via non-blocking asynchronous execution.
3. **Decision Cascade**: Integrates rule signals and model confidence scores into a unified operational outcome (`ALLOW`, `WARN`, `REVIEW`, `BLOCK`).

## Alternatives Considered
- **Pure Rules**: Too brittle, highly susceptible to circumvention and slang drift.
- **LLM/Transformer Only**: Excessive latency for obvious violations, lacks immediate emergency intervention capabilities (e.g. unambiguous lethal threats).
- **External Third-Party APIs**: High operational cost, data privacy concerns, and external dependency risks.

## Consequences
- **Positive**: Low latency on unambiguous cases, contextual verification for nuanced statements, and an explicit review queue for ambiguous content.
- **Negative**: Requires maintaining two separate detection mechanisms and calibration of joint threshold boundaries.
