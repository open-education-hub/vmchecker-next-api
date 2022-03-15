import base64
import logging
import uuid

import gitlab
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from api.core.storage import storage
from api.core.task_runner import Runner
from api.models import Task, TaskState
from api.serializer import TaskSerializer

log = logging.getLogger(__name__)


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


@api_view(["GET"])
def diff(_: Request, UUID: str) -> Response:
    return Response({"UUID": "123"})


@api_view(["POST"])
def pipeline_output(_: Request, UUID: str) -> Response:
    return Response({"UUID": "123"})


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
def healthcheck(_: Request) -> Response:
    return Response({"status": "ok"})


api_definition = [
    path("submit", view=submit),
    path("<str:UUID>/status", view=status),
    path("<str:UUID>/cancel", view=cancel),
    path("<str:UUID>/trace", view=trace),
    path("<str:UUID>/diff", view=diff),
    path("<str:UUID>/pipeline_output", view=pipeline_output),
    path("info", view=info),
    path("healthcheck", view=healthcheck),
]
