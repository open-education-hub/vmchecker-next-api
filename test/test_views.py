import base64
import json

import pytest
from django.test import Client

from api.models import Task


def test_healthcheck(client: Client):
    response = client.get("/api/v1/health")
    assert response.json()["status"] == "ok"


@pytest.mark.django_db
def test_submit_status(client: Client):
    empty_zip_data = b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    archive_data = base64.encodebytes(empty_zip_data).decode("ascii")

    response = client.post(
        "/api/v1/submit",
        json.dumps(
            {
                "gitlab_private_token": "token",
                "gitlab_project_id": 1,
                "username": "user",
                "archive": archive_data,
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200

    UUID = response.json()["UUID"]
    assert Task.objects.all().get(UUID=UUID) is not None

    response = client.get(f"/api/v1/{UUID}/status")
    assert response.json()["status"] == "new"
