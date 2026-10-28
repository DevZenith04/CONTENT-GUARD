"""ContentGuard · Transformer-based contextual analysis (LLM component).

Uses ``unitary/toxic-bert`` (DistilBERT fine-tuned for toxicity) to produce
per-category confidence scores.  The model runs entirely locally on CPU.

Output: a list of ``LLMSignal`` objects, one per category that exceeds a
minimum confidence floor.  If the model is uncertain enough, it sets
``abstain=True`` to signal that a human should review.
"""

from __future__ import annotations

import logging

import torch
from models.schemas import LLMSignal
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger("contentguard.llm")

# Map toxic-bert output labels → ContentGuard categories.
# toxic-bert labels: toxic, severe_toxic, obscene, threat, insult, identity_hate
_LABEL_MAP: dict[str, str] = {
    "threat": "threat",
    "insult": "harassment",
    "identity_hate": "hate",
    "severe_toxic": "harassment",   # mapped to harassment (previously misclassified as threat)
    "toxic": "harassment",          # general toxicity → harassment
    "obscene": "harassment",        # obscene → harassment
}

# Categories we report on
_CATEGORIES = ["threat", "harassment", "hate", "self_harm"]

# Confidence thresholds
_MIN_CONFIDENCE = 0.10   # below this we drop the signal entirely
_ABSTAIN_BAND = (0.25, 0.50)  # if confidence is in this range, set abstain=True


class TransformerAnalyzer:
    """Wraps a HuggingFace multi-label toxicity classifier."""

    def __init__(self, model_name: str = "unitary/toxic-bert") -> None:
        self.model_name = model_name
        self._tokenizer: AutoTokenizer | None = None
        self._model: AutoModelForSequenceClassification | None = None
        self._labels: list[str] = []

    async def load(self) -> None:
        """Download / cache model on startup.  Blocking but called once."""
        logger.info("Loading transformer model: %s", self.model_name)
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self._model.eval()

        # Read the model's label order from its config
        id2label = self._model.config.id2label
        self._labels = [id2label[i] for i in range(len(id2label))]
        logger.info("Model loaded — labels: %s", self._labels)

    @property
    def model_version(self) -> str:
        return f"transformer:{self.model_name}"

    def predict(self, text: str) -> list[LLMSignal]:
        """Run inference and return LLMSignal list.

        Because toxic-bert is a multi-label classifier (sigmoid output per label),
        we get independent probabilities for each toxicity type.
        """
        if self._tokenizer is None or self._model is None:
            raise RuntimeError("TransformerAnalyzer not loaded — call .load() first")

        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )

        with torch.no_grad():
            logits = self._model(**inputs).logits
            probs = torch.sigmoid(logits).squeeze(0)

        # Build per-label scores
        raw_scores: dict[str, float] = {}
        for i, label in enumerate(self._labels):
            raw_scores[label] = float(probs[i])

        # Aggregate into ContentGuard categories (take max when multiple labels map to same category)
        cat_scores: dict[str, float] = {c: 0.0 for c in _CATEGORIES}
        for label, cg_cat in _LABEL_MAP.items():
            if label in raw_scores and cg_cat in cat_scores:
                cat_scores[cg_cat] = max(cat_scores[cg_cat], raw_scores[label])

        # Self-harm: toxic-bert doesn't have a self-harm label.
        # We use a heuristic: if "toxic" is moderately high but no specific
        # category is dominant, AND the text contains self-harm keywords,
        # assign a moderate confidence.
        self_harm_keywords = [
            "kill myself", "want to die", "end it all", "hurt myself",
            "don't want to live", "suicide", "self-harm", "self harm",
        ]
        text_lower = text.lower()
        if any(kw in text_lower for kw in self_harm_keywords):
            # Boost self_harm using the general toxicity score
            base = raw_scores.get("toxic", 0.0)
            cat_scores["self_harm"] = max(cat_scores["self_harm"], min(base + 0.3, 0.95))

        # Convert to signals
        signals: list[LLMSignal] = []
        for cat in _CATEGORIES:
            conf = cat_scores[cat]
            if conf < _MIN_CONFIDENCE:
                continue
            abstain = _ABSTAIN_BAND[0] <= conf <= _ABSTAIN_BAND[1]
            signals.append(LLMSignal(
                category=cat,
                confidence=round(conf, 4),
                abstain=abstain,
            ))

        return signals
