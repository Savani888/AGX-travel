from tests.conftest import auth_headers


def test_explanations_and_alternatives(client, auth_token):
    create = client.post(
        "/v1/itineraries",
        headers=auth_headers(auth_token),
        json={"intent": {"query": "Plan a 3-day Kyoto food and culture trip"}},
    )
    itinerary_id = create.json()["itinerary_id"]

    explanations = client.get(
        f"/v1/itineraries/{itinerary_id}/explanations",
        headers=auth_headers(auth_token),
    )
    assert explanations.status_code == 200
    assert isinstance(explanations.json(), list)

    alternatives = client.get(
        f"/v1/itineraries/{itinerary_id}/alternatives",
        headers=auth_headers(auth_token),
    )
    assert alternatives.status_code == 200
    assert len(alternatives.json()) >= 1
