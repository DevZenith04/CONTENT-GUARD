# ContentGuard Evaluation Protocol & Benchmark Report

This document defines the formal scoring methodology, metric definitions, dataset requirements, and evaluation protocols for ContentGuard.

---

## 1. Formal Scoring Definitions

A moderation system produces structured actions (`ALLOW`, `WARN`, `REVIEW`, `BLOCK`) rather than raw binary classifications. Metrics are defined as follows:

### 1.1 Category-Level Scoring
- **Predicted Positive**: An item is predicted positive for category $c \in \{\text{threat}, \text{harassment}, \text{hate}, \text{self\_harm}\}$ if and only if:
  $$\text{Outcome} \in \{\text{REVIEW}, \text{BLOCK}\} \quad \land \quad c \in \text{result.categories}$$
- **Ground Truth**: Binary human annotation label $y_c \in \{0, 1\}$.
- **Metrics**: Standard True Positives ($TP_c$), False Positives ($FP_c$), False Negatives ($FN_c$), and True Negatives ($TN_c$), yielding Precision, Recall, and $F_1$:
  $$\text{Precision}_c = \frac{TP_c}{TP_c + FP_c}, \quad \text{Recall}_c = \frac{TP_c}{TP_c + FN_c}, \quad F_{1, c} = \frac{2 \cdot P_c \cdot R_c}{P_c + R_c}$$

### 1.2 Outcome-Level Scoring (Primary Product Metric)
- **Predicted Positive**:
  $$\hat{Y}_{\text{outcome}} = 1 \iff \text{Outcome} \in \{\text{REVIEW}, \text{BLOCK}\}$$
- **Ground Truth**:
  $$Y_{\text{outcome}} = 1 \iff \bigvee_{c} y_c = 1$$
- **Significance**: In production, routing an offensive comment to human review or auto-blocking prevents harm. This binary outcome is the core reliability metric for platforms.

### 1.3 Review Rate (Operational Overhead)
$$\text{Review Rate} = \frac{\sum_{i=1}^N \mathbb{I}(\text{Outcome}_i = \text{REVIEW})}{N}$$
*A system that routes 100% of inputs to human review has 100% recall but zero automation value. Review rate quantifies human moderator workload.*

### 1.4 Statistical Rigor
- **Bootstrap Confidence Intervals**: 1,000 bootstrap resamples are computed to establish 95% empirical confidence intervals for $F_1$, precision, and recall.
- **Significance Testing**: When comparing pipeline modes (e.g. `hybrid` vs `llm_only`), McNemar's test is applied to paired predictions on identical evaluation items.

---

## 2. Evaluation Datasets

### 2.1 Contamination Mitigation
Because `unitary/toxic-bert` was trained on Wikipedia/Jigsaw toxicity corpora, testing exclusively on Jigsaw risks inflated generalization scores. Evaluation uses:
1. **Curated In-House Test Suite** (`evaluation/data/dataset.jsonl`): 200+ balanced adversarial prompts, idioms ("kill it at the interview", "take out the trash"), benign finds ("find you a link"), quoted speech, counter-speech, and self-harm edge cases.
2. **Out-of-Distribution Validation**: Secondary datasets with different domain linguistics (chat, social discussion) to measure real-world drift.

---

## 3. Evaluation Runner Architecture

The offline evaluation runner (`evaluation/runner.py`) uses decoupled analysis (`pipeline.analyze`):
1. **Zero Database Pollution**: Runs analysis in-memory without creating database events or review tickets.
2. **Warm-Up Phase**: Performs 10 warmup inferences prior to timing to isolate model loading artifacts.
3. **Artifact Generation**: Outputs machine-readable JSON runs to `results/eval_<dataset_hash>_<policy_version>.json`, which is dynamically ingested and served by the `/v1/evaluation/latest` API endpoint.

---

## 4. Ablation Study Protocol

To evaluate individual architectural decisions, the runner measures:
1. **Full Hybrid**: Rules + Transformer + Abstention + Auto-block.
2. **Hybrid w/o Auto-Block**: Auto-block disabled (high-severity items routed to review).
3. **Hybrid w/o Abstain Band**: Abstention thresholds disabled (raw confidence decisions only).
4. **Threshold Sensitivity**: Threshold perturbations ($\pm 0.05$) to measure stability.

---

## 5. Error Taxonomy & Qualitative Analysis

Misclassifications are categorized into five recurring structural archetypes:
1. **Colloquial Idiom False Positives**: Benign phrases containing aggressive vocabulary ("killing it", "dead tired").
2. **Quoted Abuse**: Users reporting or quoting harassment they received.
3. **Non-Targeted Expletives**: Casual or emphatic profanity ("fucking awesome") flagged as interpersonal harassment.
4. **Metaphorical Sarcasm**: Sarcastic rhetoric slipping through rule patterns and soft LLM thresholds.
5. **Indirect Self-Harm**: Implicit expressions of severe distress lacking explicit keyword triggers.
