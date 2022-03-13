import os
import base64
from locust import HttpUser, task, between


class QuickstartUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        empty_zip_data = b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        self.archive_data = base64.encodebytes(empty_zip_data).decode("ascii")

    @task(4)
    def ping(self):
        self.client.get("/api/v1/healthcheck")

    @task(4)
    def info(self):
        self.client.get(
            f"/api/v1/info?status=waiting_for_results&amp;gitlab_project_id={os.environ.get('LOCUST_GITLAB_PROJECT_ID')}"
        )
        self.client.get(f"/api/v1/info?status=new&amp;gitlab_project_id={os.environ.get('LOCUST_GITLAB_PROJECT_ID')}")

    @task
    def submit(self):
        self.client.post(
            "/api/v1/submit",
            json={
                "archive": self.archive_data,
                "gitlab_private_token": os.environ.get("LOCUST_GITLAB_PRIVATE_TOKEN"),
                "gitlab_project_id": os.environ.get("LOCUST_GITLAB_PROJECT_ID"),
                "username": "locust.user",
            },
        )
