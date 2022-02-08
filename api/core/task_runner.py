from __future__ import annotations
import io
import os
import time
import zipfile
import base64
import logging
from datetime import datetime
from threading import Thread
from queue import SimpleQueue

import gitlab
from django.conf import settings
from django.db.models import Q

from api.models import Task, TaskState
from api.core.storage import storage


log = logging.getLogger(__name__)


class Runner():
    def __init__(self) -> None:
        self.task_queue: SimpleQueue = SimpleQueue()
        self._load_unfinished_tasks()
        self.thread_ctl = Thread(target=self._run, name='Task runner', daemon=True)
        self.thread_ctl.start()

    def submit(self, task: Task) -> None:
        self.task_queue.put(task)

    @staticmethod
    def instance() -> Runner:
        if not hasattr(Runner, '_instance'):
            Runner._instance = None

        if Runner._instance is None:
            Runner._instance = Runner()

        return Runner._instance

    def _load_unfinished_tasks(self) -> None:
        for task in Task.objects.filter(~Q(state=TaskState.done.value)).filter(~Q(state=TaskState.error.value)):
            self.task_queue.put(task)

    def _run(self) -> None:
        log.info(f'Task runner thread started (pid: {os.getpid()})')
        while True:
            try:
                task: Task = self.task_queue.get()
                log.info(f'Checking task {task.pk} with state {TaskState(task.state).name}')
                if task.state == TaskState.new.value:
                    submit_task(task)
                    self.task_queue.put(task)
                elif task.state == TaskState.waiting_for_results.value:
                    pull_task_results(task)
                    self.task_queue.put(task)
                else:
                    pass
            except Exception as e:
                log.error(f'Error on task {task.pk}: {str(e)}')
                task.state = TaskState.error.value
                task.errorInfo = str(e)
                task.save()


def submit_task(task: Task) -> None:
    gl = gitlab.Gitlab(settings.GITLAB_URL, private_token=task.gitlab_token)
    project = gl.projects.get(task.gitlab_project_id)

    branch_name = f'{task.moodle_username}-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}-{task.UUID}'
    data = {
        'branch': branch_name,
        'start_branch': 'master',
        'commit_message': 'VMChecker backend',
        'actions': [],
    }

    items = project.repository_tree(path='src', ref='master', recursive=True, per_page=100)
    paths = list(map(lambda x: x['path'], items))

    archive = io.BytesIO(storage.get(task.submission_data_id))
    zip_archive = zipfile.ZipFile(archive, 'r')
    for filename in zip_archive.namelist():
        if filename.endswith('/'):
            continue

        action = {
            'action': 'update' if filename in paths else 'create',
            'file_path': filename,
            'content': str(base64.b64encode(zip_archive.read(filename)), 'ascii'),
            'encoding': 'base64',
        }
        data['actions'].append(action)

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

    if job.status != 'success':
        return

    task.state = TaskState.done.value
    task.save()
