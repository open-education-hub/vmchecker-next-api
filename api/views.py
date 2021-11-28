import uuid
import base64

import gitlab
from django.urls import path
from rest_framework.request import Request
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.core.task_runner import Runner
from api.core.storage import storage
from api.serializer import TaskSerializer
from api.models import Task, TaskState


@api_view(['POST'])
def submit(request: Request) -> Response:
    UUID = str(uuid.uuid4())
    archive_data = base64.decodebytes(request.data['archive'].encode('ascii'))

    Runner.instance().submit(Task.objects.create(
        submission_data_id=storage.put(archive_data),
        gitlab_url=request.data['gitlab_url'],
        gitlab_token=request.data['gitlab_private_token'],
        gitlab_project_id=request.data['gitlab_project_id'],
        moodle_username=request.data['username'],
        UUID=UUID,
    ))
    return Response({ 'UUID': UUID })


@api_view(['GET'])
def status(request: Request, UUID: str) -> Response:
    task = Task.objects.get(UUID=UUID)
    return Response({ 'status': TaskState(task.state).name })


@api_view(['GET'])
def trace(request: Request, UUID: str) -> Response:
    task = Task.objects.get(UUID=UUID)
    if task.state != TaskState.done.value:
        return Response({ 'trace': '' })

    gl = gitlab.Gitlab('https://gitlab.com', private_token=task.gitlab_token)
    project = gl.projects.get(task.gitlab_project_id)
    pipeline = project.pipelines.get(task.gitlab_pipeline_id)
    pipeline_job = pipeline.jobs.list()[0]
    project_job = project.jobs.get(pipeline_job.id)

    return Response({ 'trace': base64.encodebytes(project_job.trace()) })


@api_view(['GET'])
def diff(request: Request, UUID: str) -> Response:
    return Response({ 'UUID': '123' })


@api_view(['POST'])
def pipeline_output(request: Request, UUID: str) -> Response:
    return Response({ 'UUID': '123' })


@api_view(['GET'])
def info(request: Request) -> Response:
    serializer = TaskSerializer(Task.objects.all(), many=True)
    return Response(serializer.data)


@api_view(['GET'])
def healthcheck(request: Request) -> Response:
    return Response({ 'status': 'ok' })


api_definition = [
    path('submit', view=submit),
    path('<str:UUID>/status', view=status),
    path('<str:UUID>/trace', view=trace),
    path('<str:UUID>/diff', view=diff),
    path('<str:UUID>/pipeline_output', view=pipeline_output),
    path('info', view=info),
    path('healthcheck', view=healthcheck),
]
