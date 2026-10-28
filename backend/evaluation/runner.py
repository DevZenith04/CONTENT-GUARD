"""ContentGuard · Evaluation runner (future use).

When a labelled dataset is available, this module runs all three modes
(rule_only, llm_only, hybrid) against it and computes confusion matrices,
precision, recall, F1, FPR, FNR, review rates, and latency stats.

Usage (when implemented):
    from evaluation.runner import EvaluationRunner
    runner = EvaluationRunner(pipeline)
    results = await runner.run("path/to/labelled_data.jsonl")
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("contentguard.eval")


@dataclass
class CategoryCounts:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0


@dataclass
class ModeResult:
    review_count: int = 0
    total: int = 0
    latencies: list[float] = field(default_factory=list)
    counts: dict[str, CategoryCounts] = field(default_factory=dict)


class EvaluationRunner:
    """Runs the pipeline against a labelled dataset to produce evaluation metrics."""

    def __init__(self, pipeline) -> None:
        self.pipeline = pipeline

    async def run(self, dataset_path: str) -> dict:
        """Run evaluation.  Dataset format: JSONL with fields:
            {"text": "...", "labels": {"threat": true, "harassment": false, ...}}

        Returns a dict matching the EvaluationResponse schema.
        """
        # TODO: Implement when labelled dataset is available
        logger.warning("Evaluation runner not yet implemented — returning fixture data")
        raise NotImplementedError(
            "Real evaluation requires a labelled dataset. "
            "The /v1/evaluation/latest endpoint currently returns fixture data."
        )
