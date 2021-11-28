from __future__ import annotations
import io
import time
import zipfile
import hashlib
import pathlib
from datetime import datetime
from threading import Thread
from queue import SimpleQueue

import gitlab
from git import Repo
from django.db.models import Q

from api.models import Task, TaskState
from api.core.storage import storage


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
        for task in Task.objects.filter(~Q(state=TaskState.done.value)):
            self.task_queue.put(task)

    def _run(self) -> None:
        while True:
            task: Task = self.task_queue.get()
            if task.state == TaskState.new.value:
                submit_task(task)
                self.task_queue.put(task)
            elif task.state == TaskState.waiting_for_results.value:
                pull_task_results(task)
                self.task_queue.put(task)
            else:
                pass


def submit_task(task: Task) -> None:
    folder_hash = hashlib.md5()
    folder_hash.update(task.gitlab_url.encode('ascii'))
    repo_folder = pathlib.Path('/', 'tmp', folder_hash.hexdigest())

    repo = None
    if not repo_folder.exists():
        repo = Repo.clone_from(task.gitlab_url, repo_folder)
    else:
        repo = Repo(repo_folder)

    repo.git.checkout('master')
    repo.git.pull()

    branch_name = f'{task.moodle_username}-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}-{task.UUID}'
    repo.git.checkout('-b', branch_name)

    archive = io.BytesIO(storage.get(task.submission_data_id))
    zip_archive = zipfile.ZipFile(archive, 'r')
    zip_archive.extractall(repo_folder / 'src')
    repo.git.status()
    repo.git.add('.')
    repo.git.commit('-m', 'wip')

    repo.git.push('-u', 'origin', branch_name)

    gl = gitlab.Gitlab('https://gitlab.com', private_token=task.gitlab_token)
    project = gl.projects.get(task.gitlab_project_id)
    pipelines = project.pipelines.list(ref=branch_name)
    while len(pipelines) == 0:
        pipelines = project.pipelines.list(ref=branch_name)
        time.sleep(0.1)

    task.gitlab_pipeline_id = pipelines[0].id
    task.state = TaskState.waiting_for_results.value
    task.save()


def pull_task_results(task: Task) -> None:
    gl = gitlab.Gitlab('https://gitlab.com', private_token=task.gitlab_token)
    project = gl.projects.get(task.gitlab_project_id)
    pipeline = project.pipelines.get(task.gitlab_pipeline_id)
    job = pipeline.jobs.list()[0]

    if job.status != 'success':
        return

    task.state = TaskState.done.value
    task.save()
