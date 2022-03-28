from django.test import Client


def test_healthcheck(client: Client):
    response = client.get("/api/v1/healthcheck")
    assert response.json()["status"] == "ok"
