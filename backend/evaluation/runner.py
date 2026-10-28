"""ContentGuard · Evaluation runner.

Scores the moderation pipeline on labelled datasets across all modes
(rule_only, llm_only, hybrid) without persisting events to the database.
Computes confusion matrices, precision, recall, F1, review rate, and latency.
Results are saved to backend/results/eval_<dataset_hash>_<policy_version>.json.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import statistics
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine.pipeline import Pipeline
from models.enums import Mode, Outcome
from models.schemas import (
    ConfusionCounts,
    EvaluationMeta,
    EvaluationResponse,
    LatencyStats,
    ModeEvaluation,
)

logger = logging.getLogger("contentguard.eval")

POSITIVE_OUTCOMES = {Outcome.REVIEW, Outcome.BLOCK}
CATEGORIES = ["threat", "harassment", "hate", "self_harm"]


@dataclass
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0

    def add(self, pred: bool, truth: bool) -> None:
        if pred and truth:
            self.tp += 1
        elif pred and not truth:
            self.fp += 1
        elif not pred and truth:
            self.fn += 1
        else:
            self.tn += 1

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    def to_schema(self) -> ConfusionCounts:
        return ConfusionCounts(tp=self.tp, fp=self.fp, fn=self.fn, tn=self.tn)


def dataset_hash(path: Path) -> str:
    """Return a 12-char SHA-256 hash of the dataset file."""
    content = path.read_bytes()
    return hashlib.sha256(content).hexdigest()[:12]


def load_dataset(path: Path) -> list[dict[str, Any]]:
    """Load JSONL dataset items."""
    items: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


class EvaluationRunner:
    """Runs pipeline.analyze() over a labelled dataset for all modes."""

    def __init__(self, pipeline: Pipeline | None = None) -> None:
        self.pipeline = pipeline or Pipeline()

    async def run_mode(self, items: list[dict[str, Any]], mode: Mode) -> dict[str, Any]:
        counts = {c: Counts() for c in CATEGORIES}
        outcome_counts = Counts()
        reviews = 0
        latencies: list[float] = []

        # Warm up (5 runs without timing)
        for warm_item in items[:min(5, len(items))]:
            await self.pipeline.analyze(warm_item["text"], mode)

        for item in items:
            t0 = time.perf_counter()
            result, _, _ = await self.pipeline.analyze(item["text"], mode)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            latencies.append(elapsed_ms)

            pred_positive = result.outcome in POSITIVE_OUTCOMES
            reviews += int(result.outcome == Outcome.REVIEW)

            labels = item.get("labels", {})
            ground_truth_any = any(bool(labels.get(c)) for c in CATEGORIES)
            outcome_counts.add(pred_positive, ground_truth_any)

            for c in CATEGORIES:
                pred_c = pred_positive and (c in result.categories)
                true_c = bool(labels.get(c, False))
                counts[c].add(pred_c, true_c)

        total_items = max(len(items), 1)
        sorted_latencies = sorted(latencies)
        p95_idx = max(0, int(0.95 * len(latencies)) - 1)

        median_lat = round(statistics.median(latencies)) if latencies else 0
        p95_lat = round(sorted_latencies[p95_idx]) if sorted_latencies else 0

        mode_eval = ModeEvaluation(
            review_rate=round(reviews / total_items, 4),
            latency_ms=LatencyStats(median=median_lat, p95=p95_lat),
            cost_per_1k=None,
            counts={c: counts[c].to_schema() for c in CATEGORIES},
        )

        return {
            "evaluation": mode_eval,
            "outcome_counts": {
                "tp": outcome_counts.tp,
                "fp": outcome_counts.fp,
                "fn": outcome_counts.fn,
                "tn": outcome_counts.tn,
                "precision": round(outcome_counts.precision, 4),
                "recall": round(outcome_counts.recall, 4),
                "f1": round(outcome_counts.f1, 4),
            },
        }

    async def evaluate_dataset(self, dataset_path: Path | None = None) -> EvaluationResponse:
        path = dataset_path or (Path(__file__).parent / "data" / "dataset.jsonl")
        if not path.exists():
            raise FileNotFoundError(f"Dataset not found at {path}")

        items = load_dataset(path)
        logger.info("Evaluating %d items from %s", len(items), path.name)

        # Ensure pipeline models are loaded
        await self.pipeline.startup()

        d_hash = dataset_hash(path)
        policy_ver = self.pipeline.policy_version
        model_ver = self.pipeline.model_version
        run_timestamp = datetime.now(UTC).isoformat(timespec="seconds")

        modes_eval: dict[str, ModeEvaluation] = {}
        for mode in [Mode.RULE_ONLY, Mode.LLM_ONLY, Mode.HYBRID]:
            logger.info("Running evaluation for mode: %s", mode.value)
            res = await self.run_mode(items, mode)
            modes_eval[mode.value] = res["evaluation"]

        meta = EvaluationMeta(
            dataset_hash=d_hash,
            items=len(items),
            policy_version=policy_ver,
            model_version=model_ver,
            run_at=run_timestamp,
            preview=False,
        )

        response = EvaluationResponse(meta=meta, modes=modes_eval)

        # Save results to backend/results/ directory
        results_dir = Path(__file__).resolve().parent.parent / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        out_file = results_dir / f"eval_{d_hash}_{policy_ver}.json"
        out_file.write_text(response.model_dump_json(indent=2), encoding="utf-8")

        logger.info("Evaluation results saved to %s", out_file)
        return response


async def main():
    runner = EvaluationRunner()
    resp = await runner.evaluate_dataset()
    print("Evaluation completed successfully:")
    print(resp.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
