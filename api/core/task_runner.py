from __future__ import annotations

import base64
import io
import logging
import os
import time
import zipfile
from datetime import datetime
from threading import Thread

import gitlab
from django.conf import settings
from django.db import transaction
from django.db.models import Q

from api.core.storage import storage
from api.models import Task, TaskState

log = logging.getLogger(__name__)


class Runner:
    def __init__(self) -> None:
        self.thread_ctl = Thread(target=self._run, name="Task runner", daemon=True)
        self.thread_ctl.start()

    @staticmethod
    def instance() -> Runner:
        if not hasattr(Runner, "_instance"):
            Runner._instance = None

        if Runner._instance is None:
            Runner._instance = Runner()

        return Runner._instance

    def _run(self) -> None:
        log.info(f"Task runner thread started (pid: {os.getpid()}). Gitlab: {settings.GITLAB_URL}")
        while True:
            with transaction.atomic():
                task: Task = (
                    Task.objects.filter(~Q(state=TaskState.done.value))
                    .filter(~Q(state=TaskState.error.value))
                    .select_for_update(skip_locked=True)
                    .order_by("updated_at")
                    .first()
                )
                if not task:
                    time.sleep(1)
                    continue

                try:
                    log.info(
                        f"[pid: {os.getpid()}] Checking task {task.pk}-{task.moodle_username}, with state {TaskState(task.state).name} and updated at {task.updated_at}"
                    )
                    if task.state == TaskState.new.value:
                        submit_task(task)
                    elif task.state == TaskState.waiting_for_results.value:
                        pull_task_results(task)
                    else:
                        pass
                except Exception as e:
                    log.error(f"Error on task {task.pk}: {str(e)}")
                    log.exception(e)
                    task.state = TaskState.error.value
                    task.errorInfo = str(e)
                    task.save()


def submit_task(task: Task) -> None:
    gl = gitlab.Gitlab(settings.GITLAB_URL, private_token=task.gitlab_token)
    project = gl.projects.get(task.gitlab_project_id)

    branch_name = f'{task.moodle_username}-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}-{task.UUID}'
    data = {
        "branch": branch_name,
        "start_branch": task.gitlab_branch,
        "commit_message": "VMChecker backend",
        "actions": [],
    }

    items = project.repository_tree(path="src", ref=task.gitlab_branch, recursive=True, per_page=100)
    paths = list(map(lambda x: x["path"], items))

    log.info(f"The src/ folder of task {task.pk} contains the following paths: {paths}")

    archive = io.BytesIO(storage.get(task.submission_data_id))
    zip_archive = zipfile.ZipFile(archive, "r")
    archive_namelist = zip_archive.namelist()

    log.info(f"The archive of task {task.pk} contains the following paths: {paths}")
    for filename in archive_namelist:
        if filename.endswith("/"):
            continue

        action = {
            "action": "update" if f"src/{filename}" in paths else "create",
            "file_path": f"src/{filename}",
            "content": str(base64.b64encode(zip_archive.read(filename)), "ascii"),
            "encoding": "base64",
        }
        data["actions"].append(action)

    project.commits.create(data)

    pipelines = project.pipelines.list(ref=branch_name)
    while len(pipelines) == 0:
        pipelines = project.pipelines.list(ref=branch_name)
        time.sleep(0.1)

    task.gitlab_pipeline_id = pipelines[0].id
    task.state = TaskState.waiting_for_results.value
    task.save()


def pull_task_results(task: Task) -> None:
    gl = gitlab.Gitlab(settings.GITLAB_URL, private_token=task.gitlab_token)
    project = gl.projects.get(task.gitlab_project_id)
    pipeline = project.pipelines.get(task.gitlab_pipeline_id)
    job = pipeline.jobs.list()[0]

    log.info(
        f"[pid: {os.getpid()}] Gitlab status of job {job.id} from pipeline {pipeline.id} - (task: {task.pk}-{task.moodle_username}) is {job.status}"
    )

    if job.status == "canceled":
        task.state = TaskState.error.value
        task.error_info = "CANCELED"
    elif job.status == "success":
        task.state = TaskState.done.value
    elif job.status == "failed":
        task.state = TaskState.error.value
        task.error_info = "FAILED"

    task.save()
