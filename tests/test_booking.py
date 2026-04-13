from tests.conftest import auth_headers


def test_booking_idempotency(client, auth_token):
    create = client.post(
        "/v1/itineraries",
        headers=auth_headers(auth_token),
        json={"intent": {"query": "Plan a 3-day Kyoto trip for 2 adults"}},
    )
    itinerary_id = create.json()["itinerary_id"]

    payload = {
        "itinerary_id": itinerary_id,
        "item_id": "itm-0-m1",
        "provider": "mock-hotel",
        "payload": {"check_in": "2026-06-12", "check_out": "2026-06-14"},
        "idempotency_key": "pytest-idem-1",
    }

    first = client.post("/v1/bookings/hotels", headers=auth_headers(auth_token), json=payload)
    second = client.post("/v1/bookings/hotels", headers=auth_headers(auth_token), json=payload)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["booking_id"] == second.json()["booking_id"]
