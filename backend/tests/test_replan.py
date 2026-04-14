from tests.conftest import auth_headers


def test_replan_flow(client, auth_token):
    create = client.post(
        "/v1/itineraries",
        headers=auth_headers(auth_token),
        json={"intent": {"query": "Plan a 4-day Kyoto cultural trip for 2 adults"}},
    )
    itinerary_id = create.json()["itinerary_id"]

    replan = client.post(
        f"/v1/itineraries/{itinerary_id}/replan",
        headers=auth_headers(auth_token),
        json={
            "itinerary_id": itinerary_id,
            "reason": "Heavy rain forecast",
            "disruptions": [
                {
                    "destination": "Kyoto",
                    "category": "weather",
                    "details": {"message": "Rain"},
                    "impact_score": "high",
                }
            ],
            "preserve_bookings": True,
        },
    )
    assert replan.status_code == 200
    assert replan.json()["technical_trace"]
