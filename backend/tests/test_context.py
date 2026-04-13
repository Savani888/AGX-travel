from tests.conftest import auth_headers


def test_context_weather_and_traffic(client, auth_token):
    weather = client.get("/v1/context/weather/Kyoto", headers=auth_headers(auth_token))
    assert weather.status_code == 200
    assert weather.json()["signal_type"] == "weather"

    traffic = client.get(
        "/v1/context/traffic?origin=Kyoto%20Station&destination=Gion",
        headers=auth_headers(auth_token),
    )
    assert traffic.status_code == 200
    assert traffic.json()["signal_type"] == "traffic"
