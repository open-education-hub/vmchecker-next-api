import base64
import os
import random

from locust import HttpUser, between, task


class QuickstartUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        empty_zip_data = b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        self.archive_data = base64.encodebytes(empty_zip_data).decode("ascii")
        self.UUIDs = []

    @task(3)
    def status(self):
        if len(self.UUIDs) == 0:
            return

        self.client.post(f"/api/v1/status", json={"UUID": random.choice(self.UUIDs)})

    @task
    def submit(self):
        response = self.client.post(
            "/api/v1/submit",
            json={
                "archive": self.archive_data,
                "gitlab_private_token": os.environ.get("LOCUST_GITLAB_PRIVATE_TOKEN"),
                "gitlab_project_id": os.environ.get("LOCUST_GITLAB_PROJECT_ID"),
                "username": "locust.user",
            },
        )

        self.UUIDs.append(response.json()["UUID"])
