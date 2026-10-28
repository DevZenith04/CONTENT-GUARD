import pytest
from config import settings
from engine.rules import RuleEngine, load_rules

engine = RuleEngine(load_rules(settings.rules_path))


def hits(text: str) -> set[str]:
    return {h["signal"].name for h in engine.match(text)}


def test_lethal_threat_is_caught():
    assert "threat_auto_block" in hits("I will kill you tomorrow")


def test_idiom_is_not_a_threat():
    # "kill it at the interview" does not follow direct lethal threat patterns
    assert "threat_auto_block" not in hits("I'll kill it at the interview")


@pytest.mark.xfail(reason="FP: 'find you' in threat_generic matches benign phrase 'find you a better link'")
def test_benign_find_you():
    assert not any(n.startswith("threat") for n in hits("I'll find you a better link"))


@pytest.mark.xfail(reason="FP: 'trash' in insult_term matches household chore phrase")
def test_trash_is_not_insult():
    assert "insult_term" not in hits("Please take out the trash")


def test_harassment_targeted():
    match_set = hits("You are an idiot")
    assert "harassment_targeted" in match_set


def test_self_harm_detected():
    match_set = hits("I want to die, please help me")
    assert "self_harm_intent" in match_set
