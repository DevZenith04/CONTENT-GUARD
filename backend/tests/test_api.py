from models.schemas import LLMSignal


def test_health_and_ready(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

    res = client.get("/ready")
    assert res.status_code == 200
    assert res.json() == {"status": "ready"}


def test_moderate_endpoint_success(client):
    res = client.post(
        "/v1/moderate",
        json={"text": "A friendly harmless message", "mode": "hybrid"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "request_id" in data
    assert data["outcome"] == "ALLOW"
    assert data["severity"] == "none"


def test_moderate_validation_error(client):
    # Empty text
    res = client.post("/v1/moderate", json={"text": "", "mode": "hybrid"})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


def test_moderate_text_too_long(client):
    long_text = "a" * 2005
    res = client.post("/v1/moderate", json={"text": long_text, "mode": "hybrid"})
    assert res.status_code == 422 or res.status_code == 413


def test_get_event_not_found(client):
    res = client.get("/v1/moderations/mod_UNKNOWN999")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "not_found"


def test_reviews_flow(client):
    # Seed an event that opens a review case
    client.stub.reply = [LLMSignal(category="threat", confidence=0.88, abstain=False)]
    mod_res = client.post(
        "/v1/moderate",
        json={"text": "Suspicious threat text", "mode": "hybrid"},
    )
    assert mod_res.status_code == 200
    mod_data = mod_res.json()
    assert mod_data["outcome"] == "REVIEW"

    # Fetch reviews
    reviews_res = client.get("/v1/reviews")
    assert reviews_res.status_code == 200
    reviews = reviews_res.json()
    assert len(reviews) > 0
    open_cases = [r for r in reviews if r["status"] == "open"]
    assert len(open_cases) > 0

    case_id = open_cases[0]["case_id"]

    # Submit decision
    decide_res = client.post(
        f"/v1/reviews/{case_id}/decision",
        json={"final_outcome": "BLOCK", "reason": "Confirmed threat after manual review"},
    )
    assert decide_res.status_code == 200
    decide_data = decide_res.json()
    assert decide_data["status"] == "resolved"
    assert decide_data["final_outcome"] == "BLOCK"

    # Submit decision on non-existent case
    bad_decide = client.post(
        "/v1/reviews/case_NON_EXISTENT/decision",
        json={"final_outcome": "ALLOW", "reason": "test"},
    )
    assert bad_decide.status_code == 404


def test_evaluation_latest_endpoint(client):
    res = client.get("/v1/evaluation/latest")
    assert res.status_code == 200
    data = res.json()
    assert "meta" in data
    assert "modes" in data
    assert "hybrid" in data["modes"]
