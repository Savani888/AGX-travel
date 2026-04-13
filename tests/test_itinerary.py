from tests.conftest import auth_headers


def test_create_and_get_itinerary(client, auth_token):
    create = client.post(
        "/v1/itineraries",
        headers=auth_headers(auth_token),
        json={
            "intent": {
                "query": "Plan a 4-day cultural and food trip to Kyoto for 2 adults with a budget of 1800 dollars"
            },
            "enforce_booking_readiness": False,
        },
    )
    assert create.status_code in (200, 201)
    data = create.json()
    assert len(data["days"]) == 4
    itinerary_id = data["itinerary_id"]

    get_res = client.get(f"/v1/itineraries/{itinerary_id}", headers=auth_headers(auth_token))
    assert get_res.status_code == 200
    assert get_res.json()["itinerary_id"] == itinerary_id
