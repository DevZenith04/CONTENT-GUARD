import pytest
from engine.decision import DecisionEngine
from models.enums import Outcome
from models.schemas import LLMSignal, RuleSignal


def rule(score, auto=False, cat="threat"):
    return {"signal": RuleSignal(name="r", score=score), "auto_block": auto, "category": cat}


def llm(conf, cat="threat", abstain=False):
    return LLMSignal(category=cat, confidence=conf, abstain=abstain)


@pytest.mark.parametrize("rules, llms, mode, expected", [
    # Branch 1: auto-block
    ([rule(0.97, auto=True)], [llm(0.90)], "hybrid", Outcome.BLOCK),
    ([rule(0.97, auto=True)], [], "rule_only", Outcome.BLOCK),
    ([rule(0.97, auto=True)], [llm(0.90)], "llm_only", Outcome.BLOCK),
    # Branch 2: rule score and model confidence both high
    ([rule(0.95)], [llm(0.90)], "hybrid", Outcome.BLOCK),
    # Branch 3: high model confidence alone (>= 0.90)
    ([rule(0.80)], [llm(0.90)], "hybrid", Outcome.BLOCK),
    ([], [llm(0.95)], "llm_only", Outcome.BLOCK),
    # Branch 4: rule_only routing
    ([rule(0.80)], [], "rule_only", Outcome.REVIEW),
    ([rule(0.40)], [], "rule_only", Outcome.WARN),
    # Branch 5: abstain
    ([], [llm(0.50, abstain=True)], "hybrid", Outcome.REVIEW),
    # Branch 6: review band boundary
    ([rule(0.80)], [llm(0.88)], "hybrid", Outcome.REVIEW),
    ([], [llm(0.30)], "llm_only", Outcome.REVIEW),
    ([], [llm(0.29)], "llm_only", Outcome.WARN),
    # Branch 7: rule matched, model low
    ([rule(0.40)], [llm(0.10)], "hybrid", Outcome.WARN),
    # Branch 8: weak model signal in llm_only
    ([], [llm(0.20)], "llm_only", Outcome.WARN),
    # Branch 9: nothing
    ([], [], "hybrid", Outcome.ALLOW),
])
def test_cascade(rules, llms, mode, expected):
    result = DecisionEngine().decide(rules, llms, mode)
    assert result.outcome == expected


def test_abstain_triggers_review():
    engine = DecisionEngine()
    result = engine.decide([], [llm(0.45, abstain=True)], "hybrid")
    assert result.outcome == Outcome.REVIEW
    assert "abstained" in result.explanation.lower()


def test_allow_explanation():
    engine = DecisionEngine()
    result = engine.decide([], [], "hybrid")
    assert result.outcome == Outcome.ALLOW
    assert "No configured violation detected" in result.explanation
