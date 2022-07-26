import base64
import io
import logging
import uuid
import zipfile

import gitlab
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.urls import path
from prometheus_client import Gauge
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from api.core.storage import storage
from api.models import Task, TaskState
from api.serializer import TaskSerializer

log = logging.getLogger(__name__)


tasks_new = Gauge("vmck_tasks_new", "New tasks")
tasks_waiting_for_results = Gauge("vmck_tasks_waiting_for_results", "Waiting for results tasks")
tasks_done = Gauge("vmck_tasks_done", "Done tasks")
tasks_error = Gauge("vmck_tasks_error", "Error tasks")

tasks_new.set_function(lambda: Task.objects.filter(state=TaskState.new.value).count())
tasks_waiting_for_results.set_function(lambda: Task.objects.filter(state=TaskState.waiting_for_results.value).count())
tasks_done.set_function(lambda: Task.objects.filter(state=TaskState.done.value).count())
tasks_error.set_function(lambda: Task.objects.filter(state=TaskState.error.value).count())


@api_view(["POST"])
def submit(request: Request) -> Response:
    UUID = str(uuid.uuid4())
    archive_data = base64.decodebytes(request.data["archive"].encode("ascii"))

    Task.objects.create(
        submission_data_id=storage.put(archive_data),
        gitlab_token=request.data["gitlab_private_token"],
        gitlab_project_id=request.data["gitlab_project_id"],
        moodle_username=request.data["username"],
        UUID=UUID,
    )
    return Response({"UUID": UUID})


@api_view(["GET"])
def status(_: Request, UUID: str) -> Response:
    task = Task.objects.get(UUID=UUID)
    return Response({"status": TaskState(task.state).name})


@api_view(["GET"])
def trace(_: Request, UUID: str) -> Response:
    task = Task.objects.get(UUID=UUID)
    if task.state != TaskState.done.value:
        return Response({"trace": ""})

    gl = gitlab.Gitlab(settings.GITLAB_URL, private_token=task.gitlab_token)
    project = gl.projects.get(task.gitlab_project_id)
    pipeline = project.pipelines.get(task.gitlab_pipeline_id)
    pipeline_job = pipeline.jobs.list()[0]
    project_job = project.jobs.get(pipeline_job.id)

    return Response({"trace": base64.encodebytes(project_job.trace())})


@api_view(["POST"])
@transaction.atomic
def cancel(_: Request, UUID: str) -> Response:
    task = (
        Task.objects.select_for_update()
        .filter(Q(state=TaskState.new.value) | Q(state=TaskState.waiting_for_results.value))
        .get(UUID=UUID)
    )
    if not task:
        return Response({"status": "not_present"})

    if task.state == TaskState.waiting_for_results.value:
        log.info(f"Cancelling {UUID} - (pipeline: {task.gitlab_pipeline_id})")

        gl = gitlab.Gitlab(settings.GITLAB_URL, private_token=task.gitlab_token)
        project = gl.projects.get(task.gitlab_project_id)
        project.pipelines.get(task.gitlab_pipeline_id).cancel()
    else:
        task.state = TaskState.error.value
        task.error_info = "CANCELED"
        task.save()

    return Response({"status": "ok"})


@api_view(["POST"])
def get_archive(request: Request) -> Response:
    gl = gitlab.Gitlab(settings.GITLAB_URL, private_token=request.data["gitlab_private_token"])
    project = gl.projects.get(request.data["gitlab_project_id"])

    tree = project.repository_tree(path="src", ref="master", recursive=True, per_page=100)

    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "a") as archive:
        for tree_item in tree:
            if tree_item["type"] == "tree":
                continue

            repo_path = tree_item["path"]
            f = project.files.raw(file_path=repo_path, ref="master")
            archive.writestr(repo_path[len("src/") :], f)

    archive_buffer.seek(0)
    data = archive_buffer.read()
    return Response({"diff": base64.encodebytes(data)})


@api_view(["GET"])
def info(request: Request) -> Response:
    job_status = TaskState.from_name(request.query_params.get("status"))
    project_id = request.query_params.get("gitlab_project_id")
    username = request.query_params.get("moodle_username")
    count = request.query_params.get("count")
    order = request.query_params.get("order") if request.query_params.get("order") else "desc"

    tasks = Task.objects.all()

    if job_status:
        tasks = tasks.filter(state=job_status.value)

    if project_id:
        tasks = tasks.filter(gitlab_project_id=int(project_id))

    if username:
        tasks = tasks.filter(moodle_username=username)

    tasks = tasks.order_by("-pk" if order == "desc" else "pk")

    if count:
        tasks = tasks[: int(count)]

    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def health(_: Request) -> Response:
    return Response({"status": "ok"})


api_definition = [
    path("submit", view=submit),
    path("<str:UUID>/status", view=status),
    path("<str:UUID>/cancel", view=cancel),
    path("<str:UUID>/trace", view=trace),
    path("archive", view=get_archive),
    path("info", view=info),
    path("health", view=health),
]
