def test_extract_intent_happy_path(client):
    res = client.post(
        "/v1/intent/extract",
        json={
            "query": "Plan a 3-day cultural trip to Kyoto for 2 adults with a budget of 1200 dollars"
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["destination"].lower() == "kyoto"
    assert data["duration_days"] == 3
    assert data["group_size"] == 2
    assert data["budget"] == 1200.0


def test_invalid_intent_request(client):
    res = client.post("/v1/intent/extract", json={})
    assert res.status_code in (400, 422)
    body = res.json()
    assert "error" in body
