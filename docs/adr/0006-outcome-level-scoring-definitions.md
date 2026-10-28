# ADR 0006: Outcome-Level & Category-Level Evaluation Metrics

## Context
Standard ML multi-label classification metrics (Precision, Recall, F1 on binary labels) fail to measure the true user and platform impact of content moderation systems that output operational decisions (`ALLOW`, `WARN`, `REVIEW`, `BLOCK`).

## Decision
We decouple evaluation into three distinct operational metrics:
1. **Outcome-Level Scoring**: An item is considered predicted positive if and only if it routes to `REVIEW` or `BLOCK`. Ground truth is positive if any policy violation occurred. This is the primary product metric.
2. **Category-Level Scoring**: A category is predicted positive only when the outcome is actionable (`REVIEW` or `BLOCK`) and the category is explicitly included in `result.categories`.
3. **Review Rate**: The proportion of all requests routed to human reviewers, representing the operational workload cost.

## Consequences
- **Positive**: Align statistical machine learning evaluation with actual platform risk and moderator operations.
- **Negative**: Requires custom evaluation logic (`evaluation/runner.py`) rather than generic out-of-the-box `scikit-learn` classification reports.
