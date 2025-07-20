def test_decision_engine():
    from core.decision_engine import DecisionEngine
    engine = DecisionEngine()
    info = {"price": "999"}
    verdict = engine.decide(info)
    assert "verdict" in verdict
    assert "timestamp" in verdict 